from typing import Any, Dict, List, Optional
from tools.destination_search import search_destinations


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
            # Attempt to enrich the hinted destination using the local search database
            try:
                matches = search_destinations(interests, budget, duration, preferred_region or '')
                # look for a close name match
                for m in matches:
                    if destination_hint.lower() in m.get('name', '').lower() or m.get('name', '').lower() in destination_hint.lower():
                        return [m]
            except Exception:
                pass
            return [self._build_custom_destination(destination_hint, interests, budget, duration)]

        return [self._build_custom_destination('A destination based on your prompt', interests, budget, duration)]

    def _build_custom_destination(
        self,
        destination_hint: str,
        interests: List[str],
        budget: float,
        duration: int,
    ) -> Dict[str, Any]:
        destination_name = destination_hint.strip() or 'A custom destination'
        tags = interests or ['culture']
        reason = f"The plan is being generated dynamically for {destination_name} based on the prompt details."
        estimated_daily_cost = self._estimate_daily_cost(budget, duration, tags)
        return {
            'name': destination_name,
            'region': 'Dynamic based on user prompt',
            'tags': tags,
            'attractions': [],
            'avg_daily_cost': estimated_daily_cost,
            'visa_required': 'international' in destination_name.lower() or len(destination_name.split()) > 1,
            'currency': 'INR',
            'reason': reason,
            'weather': 'Weather guidance will be derived dynamically from the destination and travel dates.',
            'best_months': 'Best travel months will be inferred from the travel season and travel dates.',
            'visa': 'Visa guidance will be generated based on the destination and nationality.',
            'recommendation_points': [reason],
        }

    def _estimate_daily_cost(self, budget: float, duration: int, interests: List[str]) -> int:
        if budget and duration:
            daily = budget / max(duration, 1)
            if 'luxury' in interests or 'honeymoon' in interests:
                return int(daily / 1.2)
            if 'budget' in interests or 'solo' in interests:
                return max(100, int(daily / 1.7))
            return max(120, int(daily / 1.4))
        return 180
