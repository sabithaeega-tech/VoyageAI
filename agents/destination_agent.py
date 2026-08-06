import json
from typing import Any, Dict, List, Optional
from providers.ollama_provider import OllamaProvider
from tools.destination_search import DESTINATIONS, _build_recommendation_metadata, search_destinations


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _destination_matches_hint(destination_name: str, hint: str) -> bool:
    normalized_hint = hint.strip().lower()
    normalized_name = destination_name.strip().lower()
    city_only = normalized_name.split(',')[0].strip()
    return normalized_hint == normalized_name or normalized_hint == city_only


class DestinationRecommendationAgent:
    def __init__(self) -> None:
        self.provider = OllamaProvider()

    def recommend(
        self,
        interests: List[str],
        budget: float,
        duration: int,
        preferred_region: str,
        destination_hint: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        interests = [interest.strip().lower() for interest in interests if interest]

        # Use LLM to recommend destinations
        prompt = (
            "You are VoyageAI's Destination Recommendation Agent. Recommend the single best travel destination (or up to 3) matching the traveler's criteria. "
            "Return only valid JSON as an array of objects. Do not include any explanations or conversational text outside the JSON. "
            "Each object in the JSON array must have the following keys:\n"
            " - 'name': string (e.g. 'Tokyo, Japan' or 'Rome, Italy')\n"
            " - 'region': string (e.g. 'Asia', 'Europe', 'North America')\n"
            " - 'tags': list of strings (e.g. ['culture', 'food'])\n"
            " - 'avg_daily_cost': number (estimated average daily cost per person in destination's local currency, or a reasonable amount in USD/INR)\n"
            " - 'visa_required': boolean (true if visa is required for typical international tourists, false otherwise)\n"
            " - 'currency': string (the 3-letter currency code, e.g. 'JPY', 'EUR', 'USD', 'INR')\n"
            " - 'attractions': list of strings (4-5 key attractions)\n"
            " - 'reason': string (compelling reason why this destination fits)\n"
            " - 'weather': string (overview of weather for typical travel seasons)\n"
            " - 'best_months': string (best months to visit)\n"
            " - 'visa': string (summary of visa rules/guidance)\n"
            " - 'recommendation_points': list of strings (bullet points summarizing recommendations)\n\n"
            f"Traveler profile:\n"
            f" - Interests: {interests}\n"
            f" - Budget: {budget}\n"
            f" - Duration: {duration} days\n"
            f" - Preferred region: {preferred_region or 'Any'}\n"
            f" - Destination Hint (if specified): {destination_hint or 'None'}\n\n"
            "Generate recommendations tailored exactly to these inputs."
        )

        try:
            response = self.provider.generate(prompt)
            content = self._extract_json_array(response)
            if content:
                results = json.loads(content)
                if isinstance(results, list) and len(results) > 0:
                    # Validate keys and types
                    validated_results = []
                    for r in results:
                        if not isinstance(r, dict):
                            continue
                        name = r.get('name', '')
                        if not name:
                            continue
                        validated_results.append({
                            'name': str(name),
                            'region': str(r.get('region', '')),
                            'tags': list(r.get('tags', [])),
                            'avg_daily_cost': float(r.get('avg_daily_cost', 150)),
                            'visa_required': bool(r.get('visa_required', False)),
                            'currency': str(r.get('currency', 'USD')).upper(),
                            'attractions': list(r.get('attractions', [])),
                            'reason': str(r.get('reason', '')),
                            'weather': str(r.get('weather', '')),
                            'best_months': str(r.get('best_months', '')),
                            'visa': str(r.get('visa', '')),
                            'recommendation_points': list(r.get('recommendation_points', [r.get('reason', '')])),
                        })
                    if validated_results:
                        return validated_results
        except Exception as e:
            # Fall back to local search in case of any error
            pass

        # Fallback to local rule-based system
        if destination_hint:
            destination_hint = destination_hint.strip()
            for destination in DESTINATIONS:
                if _destination_matches_hint(destination['name'], destination_hint):
                    return [_build_recommendation_metadata(destination, interests, budget, duration)]

            return [self._build_custom_destination(destination_hint, interests, budget, duration)]

        return search_destinations(interests, budget, duration, preferred_region)

    def _extract_json_array(self, text: str) -> str:
        text = text.strip()
        start = text.find('[')
        if start == -1:
            return ''

        depth = 0
        for index, char in enumerate(text[start:], start=start):
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]

        if text.startswith('[') and text.endswith(']'):
            return text
        return ''

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
