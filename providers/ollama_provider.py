import json
import os
from typing import Any, Callable, Dict, List, Optional

import ollama
from langchain_ollama import OllamaLLM

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
        self.client = ollama.Client(host=self.host)
        self.llm = OllamaLLM(
            model=self.model,
            base_url=self.host,
            temperature=self.temperature,
            system=self.system_prompt,
        )

    def generate(self, prompt: str) -> str:
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
        except Exception as exc:
            return f'Travel summary generation fallback: {exc}'

    def generate_with_tools(self, prompt: str, tools: Optional[List[Callable]] = None) -> str:
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
            # If the assistant invoked tools, run them locally and provide the results as tool messages,
            # then send a follow-up to let the assistant incorporate tool outputs.
            tool_calls = getattr(response.message, 'tool_calls', None)
            if content:
                return content
            if tool_calls:
                # Append assistant placeholder and then tool outputs
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
                        except Exception as e:
                            result = {'error': str(e)}
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

    def tool_search_destinations(
        self,
        interests: str,
        budget: float,
        duration: int,
        region: str,
    ) -> List[Dict[str, Any]]:
        """Search travel destinations matching the user's interests and budget.

        Args:
            interests: Comma-separated interest keywords.
            budget: User budget for the trip.
            duration: Trip duration in days.
            region: Preferred travel region.

        Returns:
            A list of matching destination records.
        """
        interest_list = [item.strip() for item in interests.split(',') if item.strip()]
        return search_destinations(interest_list, budget, duration, region)

    def tool_estimate_budget(
        self,
        destination: str,
        duration: int,
        travelers: int,
        accommodation_style: str,
    ) -> Dict[str, Any]:
        """Estimate travel budget for a selected destination."""
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
        """Return visa guidance for a destination and nationality."""
        return lookup_visa_info(destination, nationality)

    def tool_get_weather(self, destination: str, travel_date: str) -> Dict[str, str]:
        """Return weather guidance for the destination and travel date."""
        return get_weather_forecast(destination, travel_date)
