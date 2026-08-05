from typing import Any, Dict, List, Optional
from tools.destination_search import DESTINATIONS, _build_recommendation_metadata, search_destinations


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _destination_matches_hint(destination_name: str, hint: str) -> bool:
    normalized_hint = hint.strip().lower()
    normalized_name = destination_name.strip().lower()
    city_only = normalized_name.split(',')[0].strip()
    return normalized_hint == normalized_name or normalized_hint == city_only


class DestinationRecommendationAgent:
    def recommend(
        self,
        interests: List[str],
        budget: float,
        duration: int,
        preferred_region: str,
        destination_hint: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        interests = [interest.strip().lower() for interest in interests if interest]

        if destination_hint:
            destination_hint = destination_hint.strip()
            for destination in DESTINATIONS:
                if _destination_matches_hint(destination['name'], destination_hint):
                    return [_build_recommendation_metadata(destination, interests, budget, duration)]

            return [self._build_custom_destination(destination_hint, interests, budget, duration)]

        return search_destinations(interests, budget, duration, preferred_region)

    def _build_custom_destination(
        self,
        destination_hint: str,
        interests: List[str],
        budget: float,
        duration: int,
    ) -> Dict[str, Any]:
        destination_name = destination_hint.strip()
        reason = f"Selected destination from prompt: {destination_name}."
        return {
            'name': destination_name,
            'region': '',
            'tags': interests or [],
            'attractions': [],
            'avg_daily_cost': 150,
            'visa_required': False,
            'currency': 'USD',
            'reason': reason,
            'weather': 'Destination-specific weather guidance will be derived from the prompt and expected travel dates.',
            'best_months': 'Best travel months depend on the destination.',
            'visa': 'Visa requirements depend on the destination and your nationality.',
            'recommendation_points': [reason],
        }
