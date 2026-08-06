import json
import os
from typing import Any, Callable, Dict, List, Optional

try:
    import ollama
except ImportError:  # pragma: no cover - optional dependency
    ollama = None

try:
    from langchain_ollama import OllamaLLM
except ImportError:  # pragma: no cover - optional dependency
    OllamaLLM = None

from tools.budget_calculator import estimate_trip_budget
from tools.currency_converter import convert
from tools.destination_search import search_destinations
from tools.visa_lookup import lookup_visa_info
from tools.weather_service import get_weather_forecast


class OllamaProvider:
    def __init__(self) -> None:
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.temperature = float(os.getenv('OLLAMA_TEMPERATURE', '0.2'))
        self.system_prompt = os.getenv(
            'OLLAMA_SYSTEM_PROMPT',
            'You are VoyageAI, a multi-agent travel planning supervisor. Use the available tools to generate accurate travel planning summaries and assistance.',
        )
        self.client = None
        self.llm = None
        if ollama is not None:
            try:
                self.client = ollama.Client(host=self.host)
            except Exception:
                self.client = None
        if OllamaLLM is not None:
            try:
                self.llm = OllamaLLM(
                    model=self.model,
                    base_url=self.host,
                    temperature=self.temperature,
                    system=self.system_prompt,
                )
            except Exception:
                self.llm = None

    def generate(self, prompt: str) -> str:
        if self.client is None:
            return self._fallback_response(prompt)
        try:
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': prompt},
            ]
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=False,
            )
            return self._parse_chat_response(response).strip()
        except Exception:
            return self._fallback_response(prompt)

    def generate_with_tools(self, prompt: str, tools: Optional[List[Callable]] = None) -> str:
        if self.client is None:
            return self._fallback_response(prompt)
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': prompt},
        ]
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                format='',
                stream=False,
            )
            content = self._parse_chat_response(response).strip()
            tool_calls = getattr(response.message, 'tool_calls', None)
            if content:
                return content
            if tool_calls:
                messages.append({'role': 'assistant', 'content': ''})
                tool_map = {
                    'tool_search_destinations': self.tool_search_destinations,
                    'tool_estimate_budget': self.tool_estimate_budget,
                    'tool_lookup_visa': self.tool_lookup_visa,
                    'tool_get_weather': self.tool_get_weather,
                }

                for tool_call in tool_calls:
                    name = getattr(tool_call.function, 'name', None)
                    args = getattr(tool_call, 'arguments', {}) or {}
                    if name in tool_map:
                        try:
                            result = tool_map[name](**args)
                        except Exception as exc:
                            result = {'error': str(exc)}
                        messages.append(
                            {
                                'role': 'tool',
                                'name': name,
                                'content': json.dumps(result, default=str),
                            }
                        )
                    else:
                        messages.append(
                            {
                                'role': 'tool',
                                'name': name or 'unknown_tool',
                                'content': json.dumps({'error': 'Unknown tool'}, default=str),
                            }
                        )

                follow_up = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=False,
                )
                return self._parse_chat_response(follow_up).strip()
            return content
        except Exception:
            return self.generate(prompt)

    def _parse_chat_response(self, response: Any) -> str:
        if hasattr(response, 'message') and response.message is not None:
            return getattr(response.message, 'content', '') or ''
        if hasattr(response, 'content'):
            return str(response.content)
        return ''

    def _fallback_response(self, prompt: str) -> str:
        if 'itinerary' in prompt.lower():
            return 'Travel planning details are being generated locally with a structured fallback prompt.'
        return 'Travel planning guidance generated locally because the LLM backend is unavailable.'

    def tool_search_destinations(
        self,
        interests: str,
        budget: float,
        duration: int,
        region: str,
    ) -> List[Dict[str, Any]]:
        interest_list = [item.strip() for item in interests.split(',') if item.strip()]
        return search_destinations(interest_list, budget, duration, region)

    def tool_estimate_budget(
        self,
        destination: str,
        duration: int,
        travelers: int,
        accommodation_style: str,
    ) -> Dict[str, Any]:
        available = search_destinations([], 0, duration, '')
        match = next((item for item in available if item['name'].lower() == destination.lower()), None)
        if not match:
            match = available[0] if available else {'name': destination, 'avg_daily_cost': 150, 'currency': 'USD'}
        budget_data = estimate_trip_budget(match, duration, travelers, accommodation_style)
        if budget_data['currency'] != 'USD':
            budget_data['total_converted'] = convert(budget_data['total'], budget_data['currency'], 'USD')
        else:
            budget_data['total_converted'] = budget_data['total']
        return budget_data

    def tool_lookup_visa(self, destination: str, nationality: str) -> Dict[str, str]:
        return lookup_visa_info(destination, nationality)

    def tool_get_weather(self, destination: str, travel_date: str) -> Dict[str, str]:
        return get_weather_forecast(destination, travel_date)
