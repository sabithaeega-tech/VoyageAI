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

        self.memory.state.last_request = user_input
        self.memory.add_system_message('Generated travel plan and itinerary.')
        return result

    def parse_user_request(self, user_input: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        duration = self.extract_int(user_input, r'(\d+)\s*-?\s*day') or user_profile.get('duration') or self.memory.state.trip_duration or 5
        budget = self.extract_budget(user_input) or user_profile.get('budget') or self.memory.state.budget or 0
        travelers = self.extract_int(user_input, r'(\d+)\s*(traveler|travellers|people|guests)') or user_profile.get('travelers') or self.memory.state.travelers or 1
        travel_dates = self.extract_date(user_input) or user_profile.get('travel_dates') or self.memory.state.travel_dates
        nationality = user_profile.get('nationality') or self.memory.state.nationality
        currency = user_profile.get('currency', 'INR') or self.memory.state.currency or 'INR'
        interests = self.extract_interests(user_input) or user_profile.get('interests') or self.memory.state.interests or []
        preferred_region = self.extract_region(user_input) or user_profile.get('preferred_region') or self.memory.state.preferred_region
        destination_hint = self.extract_destination(user_input) or user_profile.get('destination_hint') or self.memory.state.last_destination
        travel_month = self.extract_month(user_input) or self._month_from_date(travel_dates)
        preferred_transportation = self.extract_transportation(user_input) or user_profile.get('preferred_transportation') or self.memory.state.preferred_transportation
        preferred_accommodation = self.extract_accommodation_preference(user_input) or user_profile.get('preferred_accommodation') or self.memory.state.preferred_accommodation
        travel_season = self.extract_season(user_input) or user_profile.get('travel_season') or self.memory.state.travel_season
        accommodation_style = self.extract_accommodation_style(user_input)
        if preferred_accommodation:
            accommodation_style = preferred_accommodation.lower()

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
            'accommodation_style': accommodation_style,
            'destination_hint': destination_hint,
            'preferred_transportation': preferred_transportation,
            'preferred_accommodation': preferred_accommodation,
            'travel_season': travel_season,
        }

    def extract_budget(self, text: str) -> Optional[float]:
        match = re.search(r'budget[^0-9\n\r\$€₹]*([0-9,]+(?:\.\d+)?)', text, re.IGNORECASE)
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

    def extract_date(self, text: str) -> Optional[str]:
        match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if match:
            return match.group(1)
        return None

    def extract_interests(self, text: str) -> List[str]:
        candidate_interests = ['beach', 'culture', 'food', 'nature', 'adventure', 'city', 'luxury', 'shopping', 'relaxation', 'history', 'wildlife', 'photography', 'honeymoon', 'family', 'solo', 'nightlife', 'trekking']
        matched = [word for word in candidate_interests if re.search(rf'\b{word}\b', text, re.IGNORECASE)]
        if matched:
            return matched
        return []

    def extract_region(self, text: str) -> Optional[str]:
        regions = ['Asia', 'Europe', 'North America', 'South America', 'Africa', 'Middle East', 'Oceania']
        for region in regions:
            if re.search(rf'\b{region}\b', text, re.IGNORECASE):
                return region
        return None

    def extract_destination(self, text: str) -> Optional[str]:
        patterns = [
            r'\b(?:to|in|for|destination|trip to|visit)\s+([A-Za-z][A-Za-z0-9 &\'\-\.\s]*)',
            r'\b(?:plan|suggest|travel|trip)\s+(?:a|an|the)?\s*(?:\d+\s*day\s*)?(?:trip\s+to\s+)?([A-Za-z][A-Za-z0-9 &\'\-\.\s]*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                extracted = re.split(r'\b(?:for|with|on|budget|days|day|travel|trip|and|in|of|under|around)\b', extracted, maxsplit=1)[0].strip(' ,.')
                if extracted and len(extracted.split()) <= 6:
                    return extracted
        return None

    def extract_month(self, text: str) -> Optional[str]:
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        for month in months:
            if re.search(rf'\b{month}\b', text, re.IGNORECASE):
                return month
        return None

    def _month_from_date(self, date_text: Optional[str]) -> Optional[str]:
        if not date_text:
            return None
        match = re.search(r'^(\d{4})-(\d{2})-(\d{2})$', date_text)
        if not match:
            return None
        month_num = int(match.group(2))
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        return month_names[month_num - 1]

    def extract_transportation(self, text: str) -> Optional[str]:
        if re.search(r'flight|air|fly', text, re.IGNORECASE):
            return 'flight'
        if re.search(r'car|drive|road trip', text, re.IGNORECASE):
            return 'car'
        if re.search(r'train|rail', text, re.IGNORECASE):
            return 'train'
        if re.search(r'bus', text, re.IGNORECASE):
            return 'bus'
        return None

    def extract_accommodation_preference(self, text: str) -> Optional[str]:
        if re.search(r'luxury|premium|resort|5-star', text, re.IGNORECASE):
            return 'luxury'
        if re.search(r'budget|economy|cheap|hostel', text, re.IGNORECASE):
            return 'budget'
        if re.search(r'family|homestay|villa', text, re.IGNORECASE):
            return 'family'
        return None

    def extract_season(self, text: str) -> Optional[str]:
        seasons = ['summer', 'winter', 'spring', 'autumn', 'monsoon', 'rainy']
        for season in seasons:
            if re.search(rf'\b{season}\b', text, re.IGNORECASE):
                return season
        return None

    def extract_accommodation_style(self, text: str) -> str:
        if re.search(r'budget|economy|cheap', text, re.IGNORECASE):
            return 'budget'
        if re.search(r'luxury|premium|upscale|resort', text, re.IGNORECASE):
            return 'premium'
        return 'moderate'
