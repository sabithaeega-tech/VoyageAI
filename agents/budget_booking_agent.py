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
        preferred_transportation: Optional[str] = None,
        preferred_accommodation: Optional[str] = None,
        travel_season: Optional[str] = None,
        interests: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        destination_name = destination.get('name', 'Your destination')
        destination_currency = destination.get('currency', 'USD')
        base_daily_cost = int(destination.get('avg_daily_cost', 180))
        style_multiplier = {'budget': 0.8, 'moderate': 1.0, 'premium': 1.4}.get(accommodation_style.lower(), 1.0)
        if preferred_accommodation == 'budget':
            style_multiplier = 0.8
        elif preferred_accommodation == 'luxury':
            style_multiplier = 1.5
        if interests and any(item in interests for item in ['luxury', 'honeymoon']):
            style_multiplier *= 1.1

        daily_cost = base_daily_cost * style_multiplier
        total = round(daily_cost * duration * max(travelers, 1) * 1.25)
        breakdown = {
            'flights': round(total * 0.2),
            'accommodation': round(daily_cost * duration * max(travelers, 1) * 0.45),
            'food': round(daily_cost * duration * max(travelers, 1) * 0.2),
            'transport': round(daily_cost * duration * max(travelers, 1) * 0.1),
            'activities': round(daily_cost * duration * max(travelers, 1) * 0.15),
            'shopping': round(total * 0.08),
            'contingency': round(total * 0.1),
        }
        total_with_breakdown = sum(breakdown.values())
        budget_data = {
            'destination': destination_name,
            'duration': duration,
            'travelers': travelers,
            'currency': destination_currency,
            'flights': breakdown['flights'],
            'lodging': breakdown['accommodation'],
            'food': breakdown['food'],
            'transport': breakdown['transport'],
            'activities': breakdown['activities'],
            'shopping': breakdown['shopping'],
            'contingency': breakdown['contingency'],
            'total': total_with_breakdown,
            'accommodation_style': accommodation_style,
            'breakdown': breakdown,
        }

        if currency.upper() != destination_currency.upper():
            budget_data['total_converted'] = convert(budget_data['total'], destination_currency, currency)
            for key in ['flights', 'lodging', 'food', 'transport', 'activities', 'shopping', 'contingency']:
                if key in budget_data:
                    try:
                        budget_data[key] = convert(budget_data[key], destination_currency, currency)
                    except Exception:
                        pass
            if 'breakdown' in budget_data and isinstance(budget_data['breakdown'], dict):
                for key, value in list(budget_data['breakdown'].items()):
                    try:
                        budget_data['breakdown'][key] = convert(value, destination_currency, currency)
                    except Exception:
                        pass
            budget_data['currency'] = currency.upper()
            budget_data['total'] = budget_data['total_converted']
        else:
            budget_data['total_converted'] = budget_data['total']

        budget_data['daily_budget'] = round(budget_data['total_converted'] / duration, 2) if duration else None
        budget_data['per_traveler_total'] = round(budget_data['total_converted'] / travelers, 2) if travelers else None
        budget_data['flight_total'] = budget_data.get('flights', 0)
        budget_data['flight_per_traveler'] = round(budget_data['flight_total'] / travelers, 2) if travelers else None
        budget_data.update(self._build_flight_details(destination_name, nationality))
        budget_data['activity_suggestions'] = self._build_activity_details(destination_name, interests or [])
        budget_data['hotel_suggestions'] = self._build_hotel_suggestions(destination_name, accommodation_style)
        budget_data['transport_recommendations'] = self._build_transport_recommendations(preferred_transportation)
        budget_data['food_recommendations'] = self._build_food_recommendations(destination_name, interests or [])
        budget_data['budget_requested'] = budget
        budget_data['budget_difference'] = round(budget - budget_data['total_converted'], 2) if budget else None
        budget_data['budget_friendly_advice'] = self._build_budget_advice(budget_data, accommodation_style)
        return budget_data

    def _build_budget_advice(self, budget_data: Dict[str, Any], accommodation_style: str) -> str:
        if budget_data['budget_difference'] is None:
            return 'Budget details are not available.'
        if budget_data['budget_difference'] < 0:
            return 'Your current budget is likely insufficient. Choose a more affordable stay or reduce premium activities.'
        if accommodation_style == 'premium':
            return 'The plan fits your budget and still leaves room for special experiences.'
        return 'This plan is reasonably paced and should fit your stated budget.'

    def _build_flight_details(self, destination_name: str, nationality: Optional[str]) -> Dict[str, Any]:
        route_origin = self._origin_from_nationality(nationality)
        if route_origin:
            flight_route = f'{route_origin} → {destination_name}'
        else:
            flight_route = f'{destination_name} (estimated round trip)'
        return {'flight_route': flight_route, 'flight_type': 'Round Trip', 'flight_note': 'Estimated travel cost for the route shown.'}

    def _origin_from_nationality(self, nationality: Optional[str]) -> str:
        mapping = {'indian': 'Hyderabad', 'american': 'New York', 'british': 'London', 'australian': 'Sydney'}
        if not nationality:
            return ''
        return mapping.get(nationality.strip().lower(), '')

    def _build_activity_details(self, destination_name: str, interests: List[str]) -> List[str]:
        destination_name = destination_name.lower()
        if 'food' in interests:
            return ['Local food tour', 'Street food tasting', 'Chef-led culinary experience']
        if 'nature' in interests or 'adventure' in interests:
            return ['Nature walk or trek', 'Adventure activity', 'Scenic viewpoint visit']
        if 'shopping' in interests:
            return ['Local market visit', 'Boutique shopping stop', 'Souvenir hunt']
        if 'luxury' in interests or 'honeymoon' in interests:
            return ['Luxury spa session', 'Private transfer', 'Fine-dining reservation']
        return ['Major sight visit', 'Local museum or cultural stop', 'Popular food experience']

    def _build_hotel_suggestions(self, destination_name: str, accommodation_style: str) -> List[str]:
        if accommodation_style == 'premium':
            return [f'Luxury hotel near the city center in {destination_name}', f'Boutique resort with premium amenities in {destination_name}']
        if accommodation_style == 'budget':
            return [f'Budget-friendly stay near transit in {destination_name}', f'Comfortable guesthouse with good reviews in {destination_name}']
        return [f'Mid-range hotel close to key attractions in {destination_name}', f'Serviced apartment with breakfast in {destination_name}']

    def _build_transport_recommendations(self, preferred_transportation: Optional[str]) -> List[str]:
        if preferred_transportation == 'flight':
            return ['Book an early flight to minimize transfer time.', 'Use airport transfers and ride-hailing for convenience.']
        if preferred_transportation == 'train':
            return ['Reserve train tickets early and use local rail connections.', 'Choose stations close to major attractions.']
        if preferred_transportation == 'car':
            return ['Plan a self-drive route with parking in mind.', 'Use a local driver for inter-city movement.']
        return ['Use a mix of local taxis, ride-hailing, and public transport.', 'Book major transfers in advance during busy travel months.']

    def _build_food_recommendations(self, destination_name: str, interests: List[str]) -> List[str]:
        if 'food' in interests:
            return [f'Try signature local dishes in {destination_name}', 'Book a food walking tour or market tasting']
        return [f'Try one iconic local dish in {destination_name}', 'Sample a café or street-food stop near your itinerary']
