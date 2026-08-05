from typing import Any, Dict, List, Optional
from tools.budget_calculator import estimate_trip_budget
from tools.currency_converter import convert


class BudgetBookingAgent:
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
        budget_data = estimate_trip_budget(destination, duration, travelers, accommodation_style)
        destination_currency = destination.get('currency', 'USD')

        if currency.upper() != destination_currency.upper():
            # Convert total and every monetary breakdown field to the requested currency.
            budget_data['total_converted'] = convert(budget_data['total'], destination_currency, currency)
            # Convert individual breakdown items
            for key in ['flights', 'lodging', 'food', 'transport', 'activities', 'shopping', 'contingency']:
                if key in budget_data:
                    try:
                        budget_data[key] = convert(budget_data[key], destination_currency, currency)
                    except Exception:
                        pass
            if 'breakdown' in budget_data and isinstance(budget_data['breakdown'], dict):
                for k, v in list(budget_data['breakdown'].items()):
                    try:
                        budget_data['breakdown'][k] = convert(v, destination_currency, currency)
                    except Exception:
                        pass
            budget_data['currency'] = currency.upper()
            try:
                budget_data['total'] = budget_data['total_converted']
            except Exception:
                pass
        else:
            budget_data['total_converted'] = budget_data['total']

        budget_data['total_converted'] = budget_data.get('total_converted', budget_data['total'])
        budget_data['daily_budget'] = round(budget_data['total_converted'] / duration, 2) if duration else None
        budget_data['per_traveler_total'] = round(budget_data['total_converted'] / travelers, 2) if travelers else None
        budget_data['flight_total'] = budget_data.get('flights', 0)
        budget_data['flight_per_traveler'] = round(budget_data['flight_total'] / travelers, 2) if travelers else None
        flight_metadata = self._build_flight_details(destination, nationality)
        budget_data.update(flight_metadata)
        budget_data['activity_suggestions'] = self._build_activity_details(destination)
        budget_data['hotel_suggestions'] = self._build_hotel_suggestions(destination, accommodation_style)
        budget_data['budget_requested'] = budget
        budget_data['budget_difference'] = round(budget - budget_data['total_converted'], 2) if budget else None
        budget_data['budget_friendly_advice'] = self._build_budget_advice(budget_data, accommodation_style)
        return budget_data

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
