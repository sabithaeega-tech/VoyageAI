import json
from typing import Any, Dict, List, Optional
from tools.budget_calculator import estimate_trip_budget
from tools.currency_converter import convert
from providers.ollama_provider import OllamaProvider


class BudgetBookingAgent:
    def __init__(self) -> None:
        self.provider = OllamaProvider()

    def estimate(
        self,
        destination: Dict[str, Any],
        duration: int,
        travelers: int,
        budget: float,
        currency: str,
        accommodation_style: str,
        nationality: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Calculate mathematical base estimate
        base_budget_data = estimate_trip_budget(destination, duration, travelers, accommodation_style)
        destination_currency = destination.get('currency', 'USD')
        currency = currency.upper()

        # Convert baseline values to the target currency first
        for key in ['flights', 'lodging', 'food', 'transport', 'activities', 'shopping', 'contingency', 'total']:
            if key in base_budget_data:
                try:
                    if destination_currency.upper() != currency:
                        base_budget_data[key] = convert(base_budget_data[key], destination_currency, currency)
                except Exception:
                    pass

        breakdown = base_budget_data.get('breakdown', {})
        if destination_currency.upper() != currency:
            for k, v in list(breakdown.items()):
                try:
                    breakdown[k] = convert(v, destination_currency, currency)
                except Exception:
                    pass

        base_total = base_budget_data.get('total', 0)

        # Build LLM prompt to refine/generate budget, hotel recommendations, and advice
        prompt = (
            "You are VoyageAI's Budget and Booking Agent. Your task is to estimate a realistic travel budget breakdown and recommend specific hotels and activities based on the traveler's profile.\n"
            "Here is the traveler profile:\n"
            f" - Destination: {destination.get('name', 'Unknown')}\n"
            f" - Duration: {duration} days\n"
            f" - Travelers: {travelers}\n"
            f" - Target Currency: {currency}\n"
            f" - Accommodation Style: {accommodation_style}\n"
            f" - Stated Budget: {budget or 'Flexible'}\n"
            f" - Nationality (origin hint): {nationality or 'Unknown'}\n\n"
            "We have computed a baseline mathematical estimate (in the target currency) for your reference:\n"
            f" - Baseline Total: {base_total} {currency}\n"
            f" - Baseline Breakdown: Flights: {breakdown.get('flights', 0)}, Lodging: {breakdown.get('accommodation', 0)}, Food: {breakdown.get('food', 0)}, Transport: {breakdown.get('transport', 0)}, Activities: {breakdown.get('activities', 0)}, Shopping: {breakdown.get('shopping', 0)}, Contingency: {breakdown.get('contingency', 0)}\n\n"
            "Refine this baseline budget using your knowledge of the destination and the accommodation style. Then, suggest specific, real-world hotels and activities.\n"
            "Return only valid JSON as a single object with the following keys. Do not include any explanations or conversational text outside the JSON:\n"
            " - 'flights': number (total estimated flight cost for all travelers, or a reasonable estimate in target currency)\n"
            " - 'lodging': number (total estimated lodging cost for all travelers and days)\n"
            " - 'food': number (total estimated food cost)\n"
            " - 'transport': number (total estimated local transport cost)\n"
            " - 'activities': number (total estimated activity cost)\n"
            " - 'shopping': number (total estimated shopping/misc cost)\n"
            " - 'contingency': number (estimated contingency fund)\n"
            " - 'total': number (the sum of flights, lodging, food, transport, activities, shopping, and contingency)\n"
            " - 'currency': string (the 3-letter target currency code, e.g. 'INR', 'USD', 'EUR')\n"
            " - 'flight_route': string (e.g. 'New York -> Tokyo')\n"
            " - 'flight_type': string (e.g. 'Round Trip')\n"
            " - 'flight_note': string (brief note about flight estimates)\n"
            " - 'hotel_suggestions': list of strings (3-4 specific real hotel/hostel names matching the accommodation style, e.g. ['Hotel Name (budget-friendly)', 'Cozy Guesthouse'])\n"
            " - 'activity_suggestions': list of strings (3-4 specific real activities/tours with estimated costs)\n"
            " - 'budget_friendly_advice': string (tailored advice on whether the stated budget is sufficient or how to save money)\n"
        )

        try:
            response = self.provider.generate(prompt)
            content = self._extract_json_object(response)
            if content:
                res = json.loads(content)
                if isinstance(res, dict) and 'total' in res:
                    # Validate fields and format
                    total_val = float(res.get('total', base_total))
                    budget_data = {
                        'destination': destination.get('name', 'Unknown'),
                        'duration': duration,
                        'travelers': travelers,
                        'currency': currency,
                        'flights': float(res.get('flights', 0)),
                        'lodging': float(res.get('lodging', 0)),
                        'food': float(res.get('food', 0)),
                        'transport': float(res.get('transport', 0)),
                        'activities': float(res.get('activities', 0)),
                        'shopping': float(res.get('shopping', 0)),
                        'contingency': float(res.get('contingency', 0)),
                        'total': total_val,
                        'accommodation_style': accommodation_style,
                        'breakdown': {
                            'flights': float(res.get('flights', 0)),
                            'accommodation': float(res.get('lodging', 0)),
                            'food': float(res.get('food', 0)),
                            'transport': float(res.get('transport', 0)),
                            'activities': float(res.get('activities', 0)),
                            'shopping': float(res.get('shopping', 0)),
                            'contingency': float(res.get('contingency', 0)),
                        },
                        'total_converted': total_val,
                        'daily_budget': round(total_val / duration, 2) if duration else None,
                        'per_traveler_total': round(total_val / travelers, 2) if travelers else None,
                        'flight_total': float(res.get('flights', 0)),
                        'flight_per_traveler': round(float(res.get('flights', 0)) / travelers, 2) if travelers else None,
                        'flight_route': str(res.get('flight_route', '')),
                        'flight_type': str(res.get('flight_type', 'Round Trip')),
                        'flight_note': str(res.get('flight_note', '')),
                        'activity_suggestions': list(res.get('activity_suggestions', [])),
                        'hotel_suggestions': list(res.get('hotel_suggestions', [])),
                        'budget_requested': budget,
                        'budget_difference': round(budget - total_val, 2) if budget else None,
                        'budget_friendly_advice': str(res.get('budget_friendly_advice', '')),
                    }
                    return budget_data
        except Exception as e:
            # Fall back to baseline calculation if error occurs
            pass

        # Fallback to math-based estimate
        base_budget_data['total_converted'] = base_total
        base_budget_data['daily_budget'] = round(base_total / duration, 2) if duration else None
        base_budget_data['per_traveler_total'] = round(base_total / travelers, 2) if travelers else None
        base_budget_data['flight_total'] = base_budget_data.get('flights', 0)
        base_budget_data['flight_per_traveler'] = round(base_budget_data['flight_total'] / travelers, 2) if travelers else None
        flight_metadata = self._build_flight_details(destination, nationality)
        base_budget_data.update(flight_metadata)
        base_budget_data['activity_suggestions'] = self._build_activity_details(destination)
        base_budget_data['hotel_suggestions'] = self._build_hotel_suggestions(destination, accommodation_style)
        base_budget_data['budget_requested'] = budget
        base_budget_data['budget_difference'] = round(budget - base_total, 2) if budget else None
        base_budget_data['budget_friendly_advice'] = self._build_budget_advice(base_budget_data, accommodation_style)
        return base_budget_data

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

    def _build_budget_advice(self, budget_data: Dict[str, Any], accommodation_style: str) -> str:
        if budget_data['budget_difference'] is None:
            return 'Budget details are not available.'

        if budget_data['budget_difference'] < 0:
            return (
                'Your current budget is likely insufficient for this itinerary. '
                'Consider selecting a budget accommodation style or choosing a lower-cost destination.'
            )

        if accommodation_style == 'premium':
            return (
                'Your budget can support this trip, but a moderate accommodation style will free up extra funds '
                'for experiences or souvenirs.'
            )

        return 'This plan is budget-conscious and should fit within your budget.'

    def _build_flight_details(self, destination: Dict[str, Any], nationality: Optional[str]) -> Dict[str, Any]:
        route_origin = self._origin_from_nationality(nationality)
        destination_name = destination.get('name', 'your destination')
        if route_origin:
            flight_route = f'{route_origin} → {destination_name}'
        else:
            flight_route = f'{destination_name} (round trip estimate)'

        return {
            'flight_route': flight_route,
            'flight_type': 'Round Trip',
            'flight_note': 'Estimated flight cost for the route shown.',
        }

    def _origin_from_nationality(self, nationality: Optional[str]) -> str:
        mapping = {
            'indian': 'Hyderabad',
            'american': 'New York',
            'british': 'London',
            'australian': 'Sydney',
            'canadian': 'Toronto',
            'german': 'Frankfurt',
            'french': 'Paris',
            'japanese': 'Tokyo',
        }
        if not nationality:
            return ''
        return mapping.get(nationality.strip().lower(), '')

    def _build_activity_details(self, destination: Dict[str, Any]) -> List[str]:
        destination_name = destination.get('name', '').lower()
        if 'new york' in destination_name or 'new york' in destination_name.lower():
            return [
                'Statue of Liberty Ferry',
                'Top of the Rock observation deck',
                'Broadway show ticket',
                'Museum ticket at the MET or MoMA',
            ]
        if 'paris' in destination_name.lower():
            return [
                'Eiffel Tower priority access',
                'Louvre museum ticket',
                'Seine river dinner cruise',
                'Montmartre walking tour',
            ]
        if 'bali' in destination_name.lower():
            return [
                'Ubud rice terrace tour',
                'Tanah Lot temple sunset visit',
                'Beach club day pass',
                'Balinese cooking class',
            ]
        return [
            'City landmark sightseeing',
            'Local cultural attraction or museum ticket',
            'Popular dining or food experience',
        ]

    def _build_hotel_suggestions(self, destination: Dict[str, Any], accommodation_style: str) -> List[str]:
        destination_name = destination.get('name', '').lower()
        if 'new york' in destination_name or 'new york' in destination_name.lower():
            return [
                'Pod Times Square (budget-friendly)',
                'HI NYC Hostel (social and affordable)',
                'Holiday Inn Manhattan (mid-range comfort)',
            ]
        if 'paris' in destination_name.lower():
            return [
                'Hôtel Ekta Paris (stylish mid-range)',
                'Generator Paris (budget-friendly)',
                'Novotel Paris Centre (reliable comfort)',
            ]
        return [
            'A highly rated central hotel or guesthouse',
            'A cozy boutique property near top attractions',
            'A budget-friendly stay with convenient transit access',
        ]
