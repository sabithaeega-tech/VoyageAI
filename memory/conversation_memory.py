from typing import Dict, List
from .state import TravelerState


class ConversationMemory:
    def __init__(self) -> None:
        self.state = TravelerState()
        self.history: List[Dict[str, str]] = []

    def add_user_message(self, text: str) -> None:
        self.history.append({'role': 'user', 'content': text})

    def add_system_message(self, text: str) -> None:
        self.history.append({'role': 'system', 'content': text})

    def update_state(self, **kwargs) -> None:
        key_map = {
            'duration': 'trip_duration',
            'travel_dates': 'travel_dates',
            'preferred_region': 'preferred_region',
            'travelers': 'travelers',
            'budget': 'budget',
            'currency': 'currency',
            'nationality': 'nationality',
            'interests': 'interests',
            'last_destination': 'last_destination',
        }

        for key, value in kwargs.items():
            mapped_key = key_map.get(key, key)
            if hasattr(self.state, mapped_key) and value is not None:
                setattr(self.state, mapped_key, value)

    def get_context(self) -> str:
        return ' '.join(item['content'] for item in self.history[-6:])
