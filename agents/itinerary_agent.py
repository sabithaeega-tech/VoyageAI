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
        travel_month: Optional[str] = None,
        travelers: int = 1,
        accommodation_style: str = 'moderate',
        nationality: str = '',
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
            travel_month=travel_month,
            travelers=travelers,
            accommodation_style=accommodation_style,
            nationality=nationality,
        )

        response = self._call_llm(prompt)
        itinerary = self._parse_response(
            response,
            duration,
            destination,
            interests,
            travel_month,
            accommodation_style,
            budget,
        )
        if not itinerary:
            itinerary = self._build_fallback_itinerary(
                destination,
                duration,
                interests,
                travel_month,
                accommodation_style,
                budget,
            )

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
        travel_month: Optional[str],
        travelers: int,
        accommodation_style: str,
        nationality: str,
    ) -> str:
        tags_text = ', '.join(tags) if tags else 'No specific tags'
        attractions_text = ', '.join(attractions[:5]) if attractions else 'No specific attractions listed'
        interests_text = ', '.join(interests) if interests else 'general travel interests'
        travel_dates_text = travel_dates or 'Flexible travel dates'
        travel_month_text = travel_month or 'the travel season'
        nationality_text = nationality or 'a traveler'

        return (
            'You are VoyageAI, a travel itinerary planner. Build a highly personalized, month-aware day-by-day itinerary for the user. '
            'Return only valid JSON as an array of objects with keys: day and highlights. '
            'Each day should include 4 to 6 action-oriented highlights such as arrival logistics, hotel suggestions, morning/afternoon/evening activities, meals, local experiences, and transport notes. '
            'If a travel month is provided, include a dedicated seasonal section such as "November Highlights" or "Spring highlights" that describes month-specific weather, festivals, events, foliage, markets, or local traditions. '
            'Include at least one recommendation for accommodation or hotel style, one type of local cuisine, and one activity tailored to the travel month and destination. '
            'Do not include any explanation outside the JSON array. '
            f'Destination: {destination_name}. '
            f'Tags: {tags_text}. '
            f'Key attractions: {attractions_text}. '
            f'Duration: {duration} day(s). '
            f'Travelers: {travelers}. '
            f'Accommodation style: {accommodation_style}. '
            f'Nationality: {nationality_text}. '
            f'Interests: {interests_text}. '
            f'Budget: {budget} {currency}. '
            f'Travel dates: {travel_dates_text}. '
            f'Travel month: {travel_month_text}. '
            'Use the travel month to highlight weather-appropriate experiences, seasonal festivals, and smart packing or dining choices. '
            'Balance the itinerary with arrival, immersive local culture, rest time, and departure preparation. '
            'Keep the schedule realistic, engaging, and designed for the requested duration and budget.'
        )

    def _call_llm(self, prompt: str) -> str:
        try:
            return self.provider.generate(prompt)
        except Exception:
            return ''

    def _parse_response(
        self,
        response: str,
        duration: int,
        destination: Dict[str, Any],
        interests: List[str],
        travel_month: Optional[str],
        accommodation_style: str,
        budget: float,
    ) -> List[Dict[str, Any]]:
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
            parsed.extend(
                self._extend_itinerary(
                    parsed,
                    destination,
                    duration,
                    interests,
                    travel_month,
                    accommodation_style,
                    budget,
                )
            )

        return parsed[:duration]

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

    def _extend_itinerary(
        self,
        parsed: List[Dict[str, Any]],
        destination: Dict[str, Any],
        duration: int,
        interests: List[str],
        travel_month: Optional[str],
        accommodation_style: str,
        budget: float,
    ) -> List[Dict[str, Any]]:
        if not parsed:
            return self._build_fallback_itinerary(
                destination,
                duration,
                interests,
                travel_month,
                accommodation_style,
                budget,
            )

        existing_days = len(parsed)
        missing_days = duration - existing_days
        if missing_days <= 0:
            return []

        return self._build_fallback_itinerary(
            destination,
            missing_days,
            interests,
            travel_month,
            accommodation_style,
            budget,
            start_day=existing_days + 1,
        )

    def _build_fallback_itinerary(
        self,
        destination: Dict[str, Any],
        duration: int,
        interests: List[str],
        travel_month: Optional[str],
        accommodation_style: str,
        budget: float,
        start_day: int = 1,
    ) -> List[Dict[str, Any]]:
        tags = [tag.lower() for tag in destination.get('tags', [])]
        attractions = destination.get('attractions', [])
        destination_name = destination.get('name', 'your destination')
        daily_budget_text = (
            f"Estimated daily budget: {round(budget / duration, 2)} {destination.get('currency', 'USD')}"
            if budget and duration else 'Daily budget will depend on your selected plan.'
        )

        itinerary = []
        for day_index in range(duration):
            day = start_day + day_index
            if day == start_day:
                plan = [
                    f'Arrive in {destination_name} and check into a comfortable {accommodation_style} hotel or guesthouse.',
                    'Settle in with a light local meal and a briefing on the itinerary.',
                    'Take a short orientation walk to explore the neighborhood and nearby highlights.',
                    daily_budget_text,
                ]
                seasonal = self._seasonal_highlights(travel_month, destination_name)
                if seasonal:
                    plan.extend(seasonal)
            elif day == start_day + duration - 1:
                plan = [
                    'Enjoy a final morning activity or souvenir shopping at a local market.',
                    'Have a leisurely lunch at a favorite spot before departure.',
                    'Return to your hotel to collect luggage and prepare for transfer to the airport or station.',
                    'Allow extra travel time for traffic and check-in procedures.',
                ]
            else:
                plan = self._build_day_plan(
                    tags,
                    interests,
                    day - start_day + 1,
                    attractions,
                    destination_name,
                    travel_month,
                    accommodation_style,
                )

            itinerary.append({'day': f'Day {day}', 'highlights': plan})

        return itinerary

    def _build_day_plan(
        self,
        tags: List[str],
        interests: List[str],
        day: int,
        attractions: List[str],
        destination_name: str,
        travel_month: Optional[str],
        accommodation_style: str,
    ) -> List[str]:
        plan = []
        month_note = ''
        if travel_month:
            month_note = f'Make the most of {travel_month} by choosing weather-appropriate activities.'

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
            attraction = attractions[(day - 1) % len(attractions)]
            plan.append(f'Visit {attraction} to experience the destination’s highlights.')

        if accommodation_style == 'premium':
            plan.append('Stay at a top-rated hotel or boutique property with strong reviews.')
        elif accommodation_style == 'budget':
            plan.append('Choose a comfortable budget-friendly stay close to the main attractions.')
        else:
            plan.append('Opt for a well-located mid-range hotel or guesthouse to balance comfort and cost.')

        if month_note:
            plan.append(month_note)
            plan.extend(self._seasonal_highlights(travel_month, destination_name))

        if day % 2 == 0 and 'relaxation' in tags:
            plan.append('Unwind with a relaxed afternoon at a spa, park, or seaside spot.')

        return plan

    def _seasonal_highlights(self, travel_month: Optional[str], destination_name: str) -> List[str]:
        if not travel_month:
            return []

        month = travel_month.strip().lower()
        if month == 'november':
            return [
                'November highlights: take in autumn foliage, seasonal street markets, and early holiday events.',
                'Central Park fall colors or a local nature walk are ideal November activities.',
                'Look for Thanksgiving-style parades, seasonal dining events, or local craft fairs.',
            ]

        if month == 'december':
            return [
                'December highlights: visit winter markets, festive light displays, and seasonal performances.',
                'Plan time for cozy indoor dining, local holiday treats, and warm evening strolls.',
            ]

        if month in {'march', 'april'}:
            return [
                f'{travel_month} highlights: enjoy spring blooms, local flower festivals, and mild outdoor exploration.',
                'Schedule scenic walks and park visits to see seasonal colors.',
            ]

        if month in {'june', 'july', 'august'}:
            return [
                f'{travel_month} highlights: expect warm weather, outdoor dining, and late sunsets.',
                'Include at least one water-based or cooling local activity.',
            ]

        return [
            f'{travel_month} highlights: choose weather-appropriate local experiences and seasonal cultural events.',
        ]
