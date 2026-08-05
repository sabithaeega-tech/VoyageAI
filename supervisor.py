import warnings
import re
from typing import Any, Dict, List, Optional

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

from graph import TravelPlannerGraph
from memory.conversation_memory import ConversationMemory
from tools.destination_search import DESTINATIONS


class SupervisorAgent:
    def __init__(self) -> None:
        self.memory = ConversationMemory()
        self.workflow = TravelPlannerGraph()

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

    def extract_budget(self, text: str) -> Optional[float]:
        # Prefer explicit budget mentions like "budget 200000" or "budget: 200000 INR".
        match = re.search(r"budget[^0-9\n\r\$€₹]*([0-9,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            cleaned = match.group(1).replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                return None
        # Fall back to any standalone number only if nothing else provided is a better source.
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
