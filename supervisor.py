import warnings
import re
import json
from typing import Any, Dict, List, Optional

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

from graph import TravelPlannerGraph
from memory.conversation_memory import ConversationMemory
from tools.destination_search import DESTINATIONS
from providers.ollama_provider import OllamaProvider


class SupervisorAgent:
    def __init__(self) -> None:
        self.memory = ConversationMemory()
        self.workflow = TravelPlannerGraph()
        self.provider = OllamaProvider()

    def handle_request(self, user_input: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.memory.add_user_message(user_input)
        request_data = self.parse_user_request(user_input, user_profile or {})
        request_data['last_destination'] = self.memory.state.last_destination

        if self.memory.history:
            request_data['conversation_update'] = True
        self.memory.update_state(**request_data)

        previous_destination = self.memory.state.last_destination
        if previous_destination and 'increase' in user_input.lower() and 'budget' in user_input.lower():
            user_input = f"Update my previous plan for {previous_destination}. {user_input}"

        result = self.workflow.run(request_data, self.memory)
        if result.get('destination_recommendations'):
            self.memory.state.last_destination = result['destination_recommendations'][0].get('name')

        self.memory.add_system_message('Generated travel plan and itinerary.')
        return result

    def parse_user_request(self, user_input: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        # Build LLM prompt to parse query
        prompt = (
            "You are VoyageAI's Supervisor parsing assistant. Parse the traveler's request and profile into structured data.\n"
            f"Traveler's Input: \"{user_input}\"\n"
            f"Traveler's Profile: {user_profile}\n\n"
            "Extract the following fields and return only valid JSON as a single object. Do not include any explanations or conversational text outside the JSON:\n"
            " - 'duration': integer (the trip duration in days, default to profile's duration, or 5)\n"
            " - 'budget': number (the total trip budget, default to profile's budget, or 150000.0)\n"
            " - 'travelers': integer (number of travelers, default to profile's travelers, or 1)\n"
            " - 'travel_dates': string (dates in YYYY-MM-DD format if mentioned, or null)\n"
            " - 'travel_month': string (the month of travel, e.g., 'November', if mentioned or derived from dates, or null)\n"
            " - 'nationality': string (the nationality from profile or input)\n"
            " - 'currency': string (the currency from profile, e.g. 'INR', or JPY/USD, or 'INR')\n"
            " - 'interests': list of strings (extract travel interests/styles, e.g. ['culture', 'beach', 'food'])\n"
            " - 'preferred_region': string (the region like 'Asia', 'Europe', or null)\n"
            " - 'accommodation_style': string (must be either 'budget', 'moderate', or 'premium')\n"
            " - 'destination_hint': string (the destination city/country mentioned, e.g., 'Tokyo, Japan' or 'Paris', or null)\n"
        )

        try:
            response = self.provider.generate(prompt)
            content = self._extract_json_object(response)
            if content:
                res = json.loads(content)
                if isinstance(res, dict):
                    return {
                        'request': user_input,
                        'duration': int(res.get('duration') or user_profile.get('duration') or 5),
                        'budget': float(res.get('budget') or user_profile.get('budget') or 150000.0),
                        'travelers': int(res.get('travelers') or user_profile.get('travelers') or 1),
                        'travel_dates': res.get('travel_dates') or user_profile.get('travel_dates'),
                        'travel_month': res.get('travel_month') or self._month_from_date(res.get('travel_dates')),
                        'nationality': res.get('nationality') or user_profile.get('nationality'),
                        'currency': res.get('currency') or user_profile.get('currency') or 'INR',
                        'interests': list(res.get('interests') or user_profile.get('interests') or []),
                        'preferred_region': res.get('preferred_region') or user_profile.get('preferred_region'),
                        'accommodation_style': res.get('accommodation_style') or self.extract_accommodation_style(user_input),
                        'destination_hint': res.get('destination_hint') or user_profile.get('destination_hint'),
                    }
        except Exception:
            # Fall back to regex parser if LLM fails
            pass

        # Regex fallback parser
        duration = self.extract_int(user_input, r"(\d+)\s*-?\s*day") or user_profile.get('duration') or 5
        budget = self.extract_budget(user_input) or user_profile.get('budget') or 0
        travelers = self.extract_int(user_input, r"(\d+)\s*(traveler|travellers|people|guests)") or user_profile.get('travelers') or 1
        travel_dates = self.extract_date(user_input) or user_profile.get('travel_dates')
        nationality = user_profile.get('nationality')
        currency = user_profile.get('currency', 'INR')
        interests = self.extract_interests(user_input) or user_profile.get('interests', [])
        preferred_region = self.extract_region(user_input) or user_profile.get('preferred_region')
        destination_hint = self.extract_destination(user_input) or user_profile.get('destination_hint')
        travel_month = self.extract_month(user_input) or self._month_from_date(travel_dates)

        return {
            'request': user_input,
            'duration': duration,
            'budget': budget,
            'travelers': travelers,
            'travel_dates': travel_dates,
            'travel_month': travel_month,
            'nationality': nationality,
            'currency': currency,
            'interests': interests,
            'preferred_region': preferred_region,
            'accommodation_style': self.extract_accommodation_style(user_input),
            'destination_hint': destination_hint,
        }

    def _extract_json_object(self, text: str) -> str:
        text = text.strip()
        start = text.find('{')
        if start == -1:
            return ''

        depth = 0
        for index, char in enumerate(text[start:], start=start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]

        if text.startswith('{') and text.endswith('}'):
            return text
        return ''

    def extract_budget(self, text: str) -> Optional[float]:
        # Prefer explicit budget mentions like "budget 200000" or "budget: 200000 INR".
        match = re.search(r"budget[^0-9\n\r\$€₹]*([0-9,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            cleaned = match.group(1).replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def extract_int(self, text: str, pattern: str) -> Optional[int]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extract_number(self, text: str) -> Optional[float]:
        cleaned = text.replace(',', '')
        match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def extract_date(self, text: str) -> Optional[str]:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            return match.group(1)
        return None

    def extract_interests(self, text: str) -> List[str]:
        candidate_interests = ['beach', 'culture', 'food', 'nature', 'adventure', 'city', 'luxury', 'shopping', 'relaxation']
        return [word for word in candidate_interests if re.search(rf"\b{word}\b", text, re.IGNORECASE)]

    def extract_region(self, text: str) -> Optional[str]:
        regions = ['Asia', 'Europe', 'North America', 'South America', 'Africa', 'Middle East', 'Oceania']
        for region in regions:
            if re.search(rf"\b{region}\b", text, re.IGNORECASE):
                return region
        return None

    def extract_destination(self, text: str) -> Optional[str]:
        normalized = text.lower()
        for destination in DESTINATIONS:
            name = destination['name'].lower()
            city = name.split(',')[0].strip()
            if city in normalized or name in normalized:
                return destination['name']

        pattern = re.search(
            r"\b(?:to|in|for|destination|trip to)\s+([A-Za-z][A-Za-z0-9 &'\-\.\s]*)",
            text,
            re.IGNORECASE,
        )
        if pattern:
            extracted = pattern.group(1).strip()
            extracted = re.split(r"\b(?:for|with|on|budget|days|day|travel|trip|and|in|of)\b", extracted, maxsplit=1)[0].strip(' ,.')
            if extracted:
                return extracted

        return None

    def extract_month(self, text: str) -> Optional[str]:
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        for month in months:
            if re.search(rf"\b{month}\b", text, re.IGNORECASE):
                return month
        return None

    def _month_from_date(self, date_text: Optional[str]) -> Optional[str]:
        if not date_text:
            return None
        match = re.search(r"^(\d{4})-(\d{2})-(\d{2})$", date_text)
        if not match:
            return None
        month_num = int(match.group(2))
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        return month_names[month_num - 1]

    def extract_accommodation_style(self, text: str) -> str:
        if re.search(r"budget|economy|cheap", text, re.IGNORECASE):
            return 'budget'
        if re.search(r"luxury|premium|upscale", text, re.IGNORECASE):
            return 'premium'
        return 'moderate'
