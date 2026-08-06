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
        preferred_transportation: Optional[str] = None,
        preferred_accommodation: Optional[str] = None,
        travel_season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        destination, duration, interests, budget, currency = self._validate_inputs(destination, duration, interests, budget, currency)
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
            preferred_transportation=preferred_transportation,
            preferred_accommodation=preferred_accommodation,
            travel_season=travel_season,
        )

        response = self._call_llm(prompt)
        itinerary = self._parse_response(response, duration, destination, interests, travel_month, accommodation_style, budget)
        if not itinerary:
            itinerary = self._build_dynamic_itinerary(destination, duration, interests, travel_month, accommodation_style, budget, currency, travel_season, preferred_transportation)
        return itinerary

    def _validate_inputs(self, destination: Dict[str, Any], duration: int, interests: List[str], budget: float, currency: str) -> tuple[Dict[str, Any], int, List[str], float, str]:
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

    def _build_prompt(self, destination_name: str, tags: List[str], attractions: List[str], duration: int, interests: List[str], budget: float, currency: str, travel_dates: Optional[str], travel_month: Optional[str], travelers: int, accommodation_style: str, nationality: str, preferred_transportation: Optional[str], preferred_accommodation: Optional[str], travel_season: Optional[str]) -> str:
        tags_text = ', '.join(tags) if tags else 'No specific tags'
        attractions_text = ', '.join(attractions[:5]) if attractions else 'No specific attractions listed'
        interests_text = ', '.join(interests) if interests else 'general travel interests'
        travel_dates_text = travel_dates or 'Flexible travel dates'
        travel_month_text = travel_month or 'the travel season'
        transport_text = preferred_transportation or 'flexible local transport'
        accommodation_text = preferred_accommodation or accommodation_style
        season_text = travel_season or travel_month_text
        return (
            f'Create a day-by-day travel plan for {destination_name}. '
            f'Keep the response concise and realistic. Return only valid JSON as an array of objects with keys day, highlights, morning, afternoon, evening, places_to_visit, and stay. '
            f'Use the following context: interests={interests_text}; tags={tags_text}; attractions={attractions_text}; duration={duration}; budget={budget} {currency}; travelers={travelers}; accommodation_style={accommodation_text}; transport={transport_text}; season={season_text}; travel_dates={travel_dates_text}. '
            'Each day should include morning, afternoon, and evening schedule details, 3 to 5 place recommendations, and a stay suggestion.'
        )

    def _call_llm(self, prompt: str) -> str:
        try:
            return self.provider.generate(prompt)
        except Exception:
            return ''

    def _parse_response(self, response: str, duration: int, destination: Dict[str, Any], interests: List[str], travel_month: Optional[str], accommodation_style: str, budget: float) -> List[Dict[str, Any]]:
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
            highlights = item.get('highlights') or []
            if isinstance(highlights, str):
                highlights_list = [highlights.strip()]
            elif isinstance(highlights, (list, tuple)):
                highlights_list = [self._normalize_activity_block(entry) for entry in highlights if self._normalize_activity_block(entry)]
            else:
                highlights_list = []

            morning = self._normalize_activity_block(item.get('morning') or (highlights_list[0] if highlights_list else ''))
            afternoon = self._normalize_activity_block(item.get('afternoon') or (highlights_list[1] if len(highlights_list) > 1 else ''))
            evening = self._normalize_activity_block(item.get('evening') or (highlights_list[2] if len(highlights_list) > 2 else ''))
            day_text = ' '.join(part for part in [morning, afternoon, evening] if part)
            extracted_places = self._extract_places_from_text(day_text, destination)
            fallback_places = self._extract_places_from_highlights([morning, afternoon, evening], destination)
            places_to_visit = self._normalize_places(item.get('places_to_visit') or extracted_places or fallback_places, destination, fallback_places)
            explicit_stay = item.get('stay')
            if explicit_stay is None:
                stay_text = self._build_day_stay_text(destination, accommodation_style, places_to_visit)
            else:
                stay_text = self._normalize_stay(explicit_stay, destination, accommodation_style)
            parsed.append({
                'day': item.get('day') or f'Day {idx + 1}',
                'highlights': highlights_list,
                'morning': morning,
                'afternoon': afternoon,
                'evening': evening,
                'places_to_visit': places_to_visit,
                'stay': stay_text,
            })
        if len(parsed) < duration:
            parsed.extend(self._extend_itinerary(parsed, destination, duration, interests, travel_month, accommodation_style, budget))
        return parsed[:duration]

    def _normalize_activity_block(self, value: Any) -> str:
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple)):
            parts = [self._format_activity_item(item) for item in value if self._format_activity_item(item)]
            return ' • '.join(parts)
        if isinstance(value, dict):
            return self._format_activity_item(value)
        return str(value)

    def _format_activity_item(self, item: Any) -> str:
        if isinstance(item, dict):
            activity = item.get('activity') or item.get('name') or item.get('title') or ''
            description = item.get('description') or item.get('details') or ''
            duration = item.get('duration')
            if activity and description:
                return f"{activity} ({duration} hrs): {description}" if duration else f"{activity}: {description}"
            if activity:
                return f"{activity} ({duration} hrs)" if duration else str(activity)
            if description:
                return str(description)
            return ', '.join(f"{key}: {value}" for key, value in item.items() if value is not None)
        return str(item)

    def _normalize_places(self, value: Any, destination: Dict[str, Any], fallback: Optional[List[str]] = None) -> List[str]:
        if isinstance(value, list):
            places = []
            for item in value:
                if isinstance(item, dict):
                    name = item.get('name') or item.get('activity') or item.get('title')
                    if name:
                        places.append(str(name))
                elif isinstance(item, str) and item.strip():
                    places.append(item.strip())
            if places:
                return places[:4]
        elif isinstance(value, dict):
            name = value.get('name') or value.get('activity') or value.get('title')
            if name:
                return [str(name)]
        if fallback:
            return fallback[:4]
        destination_name = destination.get('name', 'your destination')
        return [destination_name]

    def _normalize_stay(self, value: Any, destination: Dict[str, Any], accommodation_style: str) -> str:
        if value is None:
            return self._suggest_stay(destination, accommodation_style)
        if isinstance(value, dict):
            parts = []
            if value.get('type'):
                parts.append(str(value['type']))
            if value.get('rating') is not None:
                parts.append(f"Rating: {value['rating']}")
            if value.get('price') is not None:
                parts.append(f"Price: {value['price']}")
            if parts:
                return ', '.join(parts)
        if isinstance(value, (list, tuple)):
            formatted = [self._format_activity_item(item) for item in value if self._format_activity_item(item)]
            if formatted:
                return ' • '.join(formatted)
        if isinstance(value, str):
            return value.strip() or self._suggest_stay(destination, accommodation_style)
        return self._suggest_stay(destination, accommodation_style)

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

    def _extend_itinerary(self, parsed: List[Dict[str, Any]], destination: Dict[str, Any], duration: int, interests: List[str], travel_month: Optional[str], accommodation_style: str, budget: float) -> List[Dict[str, Any]]:
        if not parsed:
            return self._build_dynamic_itinerary(destination, duration, interests, travel_month, accommodation_style, budget, 'INR', None, None)
        existing_days = len(parsed)
        missing_days = duration - existing_days
        if missing_days <= 0:
            return []
        return self._build_dynamic_itinerary(destination, missing_days, interests, travel_month, accommodation_style, budget, 'INR', None, None, start_day=existing_days + 1)

    def _build_fallback_itinerary(self, destination: Dict[str, Any], duration: int, interests: List[str], travel_month: Optional[str], accommodation_style: str, budget: float, start_day: int = 1) -> List[Dict[str, Any]]:
        return self._build_dynamic_itinerary(destination, duration, interests, travel_month, accommodation_style, budget, 'INR', None, None, start_day=start_day)

    def _build_dynamic_itinerary(self, destination: Dict[str, Any], duration: int, interests: List[str], travel_month: Optional[str], accommodation_style: str, budget: float, currency: str, travel_season: Optional[str], preferred_transportation: Optional[str], start_day: int = 1) -> List[Dict[str, Any]]:
        destination_name = destination.get('name', 'your destination')
        tags = [tag.lower() for tag in destination.get('tags', [])]
        attractions = [str(item) for item in destination.get('attractions', []) if item]
        suggested_places = self._suggest_places_for_destination(destination_name, interests, travel_month or travel_season, attractions)
        itinerary: List[Dict[str, Any]] = []
        for day_index in range(duration):
            day_number = start_day + day_index
            morning = self._build_morning_plan(destination_name, interests, travel_month, travel_season, day_number, suggested_places)
            afternoon = self._build_afternoon_plan(destination_name, interests, attractions, suggested_places, day_number)
            evening = self._build_evening_plan(destination_name, interests, travel_month, travel_season, suggested_places)
            places = self._extract_places_from_highlights([morning, afternoon, evening], destination)
            if suggested_places and (destination_name.lower() in {'kashmir', 'bali'} or len(places) < 2):
                places = suggested_places[:4]
            if not places:
                places = [destination_name]
            itinerary.append({
                'day': f'Day {day_number}',
                'highlights': [morning, afternoon, evening],
                'morning': morning,
                'afternoon': afternoon,
                'evening': evening,
                'places_to_visit': places[:4],
                'stay': self._suggest_stay_for_day(destination, accommodation_style, places),
            })
        return itinerary

    def _build_morning_plan(self, destination_name: str, interests: List[str], travel_month: Optional[str], travel_season: Optional[str], day_number: int, suggested_places: List[str]) -> str:
        interest_text = ', '.join(interests) if interests else 'local highlights'
        season_text = travel_season or travel_month or 'the season'
        primary_place = suggested_places[0] if suggested_places else destination_name
        return f"Day {day_number} morning: start with a local breakfast and visit {primary_place} in {destination_name}, a great fit for your {interest_text} interests, with a weather-friendly plan for {season_text}."

    def _build_afternoon_plan(self, destination_name: str, interests: List[str], attractions: List[str], suggested_places: List[str], day_number: int) -> str:
        if attractions:
            attraction = attractions[(day_number - 1) % len(attractions)] if attractions else destination_name
            return f"Day {day_number} afternoon: continue with {attraction} and explore nearby food, shopping, or cultural spots suited to your interests."
        if suggested_places:
            second_place = suggested_places[1] if len(suggested_places) > 1 else suggested_places[0]
            return f"Day {day_number} afternoon: explore {second_place} and nearby local experiences around {destination_name}."
        return f"Day {day_number} afternoon: explore hidden gems, local markets, or scenic viewpoints around {destination_name}."

    def _build_evening_plan(self, destination_name: str, interests: List[str], travel_month: Optional[str], travel_season: Optional[str], suggested_places: List[str]) -> str:
        season_text = travel_season or travel_month or 'the season'
        if 'food' in interests or 'nightlife' in interests:
            dinner_place = suggested_places[2] if len(suggested_places) > 2 else suggested_places[0]
            return f"Evening: enjoy a curated dinner experience near {dinner_place} and a relaxed night walk while keeping the plan adaptable for {season_text}."
        return f"Evening: unwind with a local cultural activity or scenic view around {destination_name} based on the weather."

    def _suggest_places_for_destination(self, destination_name: str, interests: List[str], travel_month: Optional[str], attractions: List[str]) -> List[str]:
        destination_name_lower = destination_name.lower()
        if 'kashmir' in destination_name_lower:
            base_places = ['Dal Lake', 'Gulmarg', 'Pahalgam', 'Sonmarg', 'Shankaracharya Temple', 'Betaab Valley']
            if 'food' in interests:
                base_places.insert(1, 'Traditional Kashmiri Restaurant')
            if 'nature' in interests:
                base_places.insert(2, 'Ningle Lake')
            return base_places
        if 'bali' in destination_name_lower:
            return ['Ubud Monkey Forest', 'Ubud Art Market', 'Campuhan Ridge Walk', 'Kuta Beach']
        if attractions:
            return attractions[:4]
        return [destination_name]

    def _suggest_stay_for_day(self, destination: Dict[str, Any], accommodation_style: str, places_to_visit: List[str]) -> str:
        return self._build_day_stay_text(destination, accommodation_style, places_to_visit)

    def _extract_places_from_text(self, text: str, destination: Dict[str, Any]) -> List[str]:
        if not text:
            return []
        candidates: List[str] = []
        patterns = [
            r'(?:visit|explore|continue with|check-in at|check in at|sunset view at|stay at|view at)\s+([^\.]+)',
            r'\b(?:at)\s+([^\.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                chunk = match.group(1).strip()
                parts = re.split(r'\s*(?:,| and | & )\s*', chunk)
                for part in parts:
                    cleaned = re.sub(r'^(the|a|an)\s+', '', part.strip(), flags=re.IGNORECASE)
                    if cleaned and cleaned.lower() not in {'day', 'morning', 'afternoon', 'evening', 'check', 'in', 'at', 'and', 'the', 'sunset', 'view'}:
                        candidates.append(cleaned)
        if not candidates:
            for match in re.finditer(r'\b([A-Z][a-zA-Z0-9\-\'’]+(?:\s+[A-Z][a-zA-Z0-9\-\'’]+){0,4})\b', text):
                place = match.group(1).strip()
                if place.lower() not in {'day', 'morning', 'afternoon', 'evening', 'check', 'in', 'at', 'and', 'the', 'sunset', 'view'}:
                    candidates.append(place)
        attraction_names = [str(item) for item in destination.get('attractions', []) if item]
        for attraction in attraction_names:
            if attraction not in candidates:
                candidates.append(attraction)
        if not candidates:
            return [destination.get('name', 'your destination')]
        return list(dict.fromkeys(candidates))[:4]

    def _extract_places_from_highlights(self, highlights: List[str], destination: Dict[str, Any]) -> List[str]:
        places: List[str] = []
        for highlight in highlights:
            if not isinstance(highlight, str):
                continue
            match = re.search(r'(?:visit|explore|continue with|check-in at|sunset view at)\s+([^\.]+)', highlight, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if place and 'stay' not in place.lower() and 'hotel' not in place.lower():
                    places.append(place)
        attraction_names = [str(item) for item in destination.get('attractions', []) if item]
        for attraction in attraction_names:
            if attraction not in places:
                places.append(attraction)
        if not places:
            places.append(destination.get('name', 'your destination'))
        return places[:4]

    def _build_day_stay_text(self, destination: Dict[str, Any], accommodation_style: str, places_to_visit: List[str]) -> str:
        destination_name = destination.get('name', 'your destination')
        primary_places = [place for place in places_to_visit if isinstance(place, str) and place.strip()][:2]
        if primary_places:
            nearby = ', '.join(primary_places)
            if accommodation_style.lower() == 'budget':
                return f'Stay at a well-rated budget hotel near {nearby} in {destination_name}.'
            if accommodation_style.lower() == 'premium':
                return f'Stay at a boutique property close to {nearby} in {destination_name}.'
            return f'Stay at a comfortable mid-range hotel close to {nearby} in {destination_name}.'
        return self._suggest_stay(destination, accommodation_style)

    def _suggest_stay(self, destination: Dict[str, Any], accommodation_style: str) -> str:
        destination_name = destination.get('name', 'your destination')
        style = accommodation_style.lower()
        if style == 'premium':
            return f'Stay at a premium hotel or boutique property near the main attractions in {destination_name}.'
        if style == 'budget':
            return f'Stay at a well-rated budget hotel or guesthouse with easy access to transit in {destination_name}.'
        return f'Stay at a mid-range hotel or serviced apartment in {destination_name} with convenient access to key sights.'
