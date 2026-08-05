import json
import re
from typing import Any, Dict, List, Optional

from providers.ollama_provider import OllamaProvider


class ItineraryPlannerAgent:
    def __init__(self) -> None:
        self.provider = OllamaProvider()

    def generate(
        self,
        destination: Dict[str, Any],
        duration: int,
        interests: List[str],
        budget: float = 0.0,
        currency: str = 'USD',
        travel_dates: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        destination, duration, interests, budget, currency = self._validate_inputs(
            destination,
            duration,
            interests,
            budget,
            currency,
        )

        destination_details = self._collect_destination_details(destination)
        prompt = self._build_prompt(
            destination_name=destination['name'],
            tags=destination_details['tags'],
            attractions=destination_details['attractions'],
            duration=duration,
            interests=interests,
            budget=budget,
            currency=currency,
            travel_dates=travel_dates,
        )

        response = self._call_llm(prompt)
        itinerary = self._parse_response(response, duration)
        if not itinerary:
            itinerary = self._build_fallback_itinerary(destination, duration, interests)

        return itinerary

    def _validate_inputs(
        self,
        destination: Dict[str, Any],
        duration: int,
        interests: List[str],
        budget: float,
        currency: str,
    ) -> tuple[Dict[str, Any], int, List[str], float, str]:
        if not destination or not isinstance(destination, dict):
            destination = {'name': 'your destination', 'tags': [], 'attractions': []}

        duration = max(1, duration or 1)
        interests = [interest.strip().lower() for interest in interests if isinstance(interest, str) and interest.strip()]
        budget = float(budget or 0.0)
        currency = currency or 'USD'

        destination.setdefault('name', 'your destination')
        destination.setdefault('tags', [])
        destination.setdefault('attractions', [])

        return destination, duration, interests, budget, currency

    def _collect_destination_details(self, destination: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tags': [str(tag).lower() for tag in destination.get('tags', []) if tag],
            'attractions': [str(attraction) for attraction in destination.get('attractions', []) if attraction],
            'local_name': destination.get('name', 'your destination'),
        }

    def _build_prompt(
        self,
        destination_name: str,
        tags: List[str],
        attractions: List[str],
        duration: int,
        interests: List[str],
        budget: float,
        currency: str,
        travel_dates: Optional[str],
    ) -> str:
        tags_text = ', '.join(tags) if tags else 'No specific tags'
        attractions_text = ', '.join(attractions[:5]) if attractions else 'No specific attractions listed'
        interests_text = ', '.join(interests) if interests else 'general travel interests'
        travel_dates_text = travel_dates or 'Flexible travel dates'

        return (
            'You are VoyageAI, a travel itinerary planner. Use destination context and user preferences to build a day-by-day itinerary. '
            'Return only valid JSON in the format: [\n  {"day": "Day 1", "highlights": ["...", "..."]}, ...\n]. '
            'Do not include any explanation outside the JSON array. '
            f'Destination: {destination_name}. '
            f'Tags: {tags_text}. '
            f'Key attractions: {attractions_text}. '
            f'Duration: {duration} day(s). '
            f'Interests: {interests_text}. '
            f'Budget: {budget} {currency}. '
            f'Travel dates: {travel_dates_text}. '
            'If there is insufficient attraction context, create a balanced itinerary using popular activities and local culture. '
            'Each itinerary day should include 3 to 5 highlight items. '
            'Keep the itinerary realistic, diverse, and tailored to the destination and interests.'
        )

    def _call_llm(self, prompt: str) -> str:
        try:
            return self.provider.generate(prompt)
        except Exception:
            return ''

    def _parse_response(self, response: str, duration: int) -> List[Dict[str, Any]]:
        if not response:
            return []

        content = self._extract_json_array(response)
        if not content:
            return []

        try:
            raw_itinerary = json.loads(content)
        except json.JSONDecodeError:
            return []

        if not isinstance(raw_itinerary, list):
            return []

        parsed: List[Dict[str, Any]] = []
        for idx, item in enumerate(raw_itinerary):
            if not isinstance(item, dict):
                continue
            day_label = item.get('day') or f'Day {idx + 1}'
            highlights = item.get('highlights') or []
            if isinstance(highlights, str):
                highlights = [highlights]
            highlights_list = [str(entry).strip() for entry in highlights if str(entry).strip()]
            parsed.append({'day': day_label, 'highlights': highlights_list})

        if len(parsed) < duration:
            return []

        return parsed

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

    def _build_fallback_itinerary(
        self,
        destination: Dict[str, Any],
        duration: int,
        interests: List[str],
    ) -> List[Dict[str, Any]]:
        tags = [tag.lower() for tag in destination.get('tags', [])]
        attractions = destination.get('attractions', [])
        destination_name = destination.get('name', 'your destination')

        itinerary = []
        for day in range(1, duration + 1):
            if day == 1:
                plan = [
                    f'Arrive in {destination_name} and settle into your accommodation.',
                    'Take a gentle orientation walk to get a feel for the neighborhood.',
                    'Enjoy dinner at a popular local restaurant to taste regional specialties.',
                ]
            elif day == duration:
                plan = [
                    'Spend the morning on last-minute sightseeing or souvenir shopping.',
                    'Relax at a café or park before departure.',
                    'Prepare for departure and transfer to the airport or station.',
                ]
            else:
                plan = self._build_day_plan(tags, interests, day, attractions, destination_name)

            itinerary.append({'day': f'Day {day}', 'highlights': plan})

        return itinerary

    def _build_day_plan(
        self,
        tags: List[str],
        interests: List[str],
        day: int,
        attractions: List[str],
        destination_name: str,
    ) -> List[str]:
        plan = []
        if 'culture' in tags or 'art' in tags:
            plan.extend([
                'Visit an iconic museum or historic landmark.',
                'Explore a scenic neighborhood with local architecture and galleries.',
                'Enjoy lunch at a café known for regional specialties.',
            ])
        elif 'beach' in tags:
            plan.extend([
                'Spend the morning relaxing on the beach or at a seaside resort.',
                'Try a water-based activity like snorkeling or a boat ride.',
                'Watch the sunset from a coastal viewpoint and dine by the water.',
            ])
        elif 'city' in tags:
            plan.extend([
                'Discover must-see city sights and famous landmarks.',
                'Explore a lively market district or shopping street.',
                'Sample local street food or a trendy restaurant experience.',
            ])
        elif 'nature' in tags or 'adventure' in tags:
            plan.extend([
                'Take an outdoor nature hike or scenic drive.',
                'Enjoy a picnic lunch in a beautiful natural setting.',
                'Finish the day with panoramic views or a gentle nature walk.',
            ])
        else:
            plan.extend([
                'Discover the destination through its top attractions.',
                'Enjoy a local dining experience with regional flavors.',
                'Relax in the evening with a cultural or entertainment activity.',
            ])

        if 'food' in tags or 'food' in interests:
            food_activity = 'Book a local food tour or tasting experience.'
            if 1 <= len(plan) < 4:
                plan.insert(1, food_activity)
            else:
                plan.append(food_activity)

        if attractions:
            attraction = attractions[(day - 2) % len(attractions)]
            plan.append(f'Visit {attraction} to experience the destination’s highlights.')

        if day % 2 == 0 and 'relaxation' in tags:
            plan.append('Unwind with a relaxed afternoon at a spa, park, or seaside spot.')

        return plan
