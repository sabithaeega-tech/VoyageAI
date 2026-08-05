from typing import Any, Dict
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
                        # leave the original value if conversion fails
                        pass
            if 'breakdown' in budget_data and isinstance(budget_data['breakdown'], dict):
                for k, v in list(budget_data['breakdown'].items()):
                    try:
                        budget_data['breakdown'][k] = convert(v, destination_currency, currency)
                    except Exception:
                        pass
            budget_data['currency'] = currency.upper()
            # Keep the primary 'total' field consistent with converted currency for display.
            try:
                budget_data['total'] = budget_data['total_converted']
            except Exception:
                pass
        else:
            budget_data['total_converted'] = budget_data['total']

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
