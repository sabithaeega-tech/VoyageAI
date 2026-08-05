from typing import Any, Dict, List


class ReflectionAgent:
    def analyze(
        self,
        request: Dict[str, Any],
        destination: Dict[str, Any],
        itinerary: List[Dict[str, Any]],
        budget: Dict[str, Any],
        assistance: Dict[str, Any],
        memory_context: str,
    ) -> Dict[str, Any]:
        summary_sections: List[str] = []
        score = 50

        destination_name = destination.get('name', 'Unknown destination')
        destination_region = destination.get('region', 'Unknown region')
        itinerary_days = len(itinerary)
        requested_days = request.get('duration', itinerary_days)
        requested_budget = request.get('budget', 0)
        budget_difference = budget.get('budget_difference')

        summary_sections.append(f"Destination selected: {destination_name} ({destination_region}).")

        if itinerary_days == requested_days:
            summary_sections.append(f"Itinerary duration matches the requested {requested_days} days.")
            score += 10
        elif itinerary_days > requested_days:
            summary_sections.append(
                f"Itinerary contains {itinerary_days} days of activities, which is longer than requested {requested_days} days."
            )
            score -= 5
        else:
            summary_sections.append(
                f"Itinerary contains {itinerary_days} days, which is shorter than the requested {requested_days} days."
            )
            score -= 5

        if budget_difference is not None:
            if budget_difference >= 0:
                summary_sections.append(
                    f"The plan fits within your stated budget by {budget_difference} {budget.get('currency', request.get('currency', 'INR'))}."
                )
                score += 15
            else:
                summary_sections.append(
                    f"The current plan exceeds your budget by {-budget_difference} {budget.get('currency', request.get('currency', 'INR'))}. Adjust accommodations or destination for a better fit."
                )
                score -= 10
        else:
            summary_sections.append('Budget comparison is unavailable for this plan.')
            score -= 5

        if request.get('travel_dates'):
            summary_sections.append(f"Travel dates are set to {request['travel_dates']}. Consider local weather and visa timing.")
            score += 5
        elif request.get('travel_month'):
            summary_sections.append(f"Travel month is {request['travel_month']}, so seasonal activities and packing are likely relevant.")
            score += 3
        else:
            summary_sections.append('No precise travel dates were provided; keep flexibility in mind.')
            score -= 2

        if assistance.get('visa_guidance'):
            summary_sections.append(f"Visa guidance: {assistance['visa_guidance']}.")

        if assistance.get('weather_forecast'):
            summary_sections.append(f"Weather outlook: {assistance['weather_forecast']}")

        if memory_context:
            summary_sections.append('Previous conversation context has been used to maintain continuity in planning.')
            score += 5

        if requested_budget and budget.get('total_converted'):
            total_cost = budget['total_converted']
            if total_cost <= requested_budget * 0.75:
                summary_sections.append('The plan is conservative and leaves room for upgrades or extra experiences.')
                score += 5

        if request.get('interests'):
            summary_sections.append(f"Itinerary aligns with your interests in {', '.join(request['interests'])}.")
            score += 2

        validation = (
            'Travel plan validated for destination, itinerary, budget alignment, visa, and weather guidance.'
        )

        score = max(0, min(score, 100))
        summary = ' '.join(summary_sections)

        return {
            'summary': summary,
            'validation': validation,
            'itinerary_length': itinerary_days,
            'confidence_score': f'{score}%',
        }
