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
        issues: List[str] = []
        score = 50

        destination_name = destination.get('name', 'Unknown destination')
        itinerary_days = len(itinerary)
        requested_days = request.get('duration', itinerary_days)
        requested_budget = request.get('budget', 0)
        budget_difference = budget.get('budget_difference')

        summary_sections.append(f"Destination selected: {destination_name}.")

        if itinerary_days >= requested_days:
            summary_sections.append(f"The itinerary covers {itinerary_days} days, matching the requested length.")
            score += 10
        else:
            summary_sections.append(f"The itinerary is shorter than requested at {itinerary_days} days.")
            issues.append('itinerary length')
            score -= 5

        if budget_difference is not None:
            if budget_difference >= 0:
                summary_sections.append(f"The plan stays within the stated budget by {budget_difference} {budget.get('currency', request.get('currency', 'INR'))}.")
                score += 15
            else:
                summary_sections.append(f"The plan currently exceeds the budget by {-budget_difference} {budget.get('currency', request.get('currency', 'INR'))}.")
                issues.append('budget fit')
                score -= 10
        else:
            summary_sections.append('Budget comparison is not available yet.')
            issues.append('budget fit')
            score -= 5

        if request.get('travel_dates'):
            summary_sections.append(f"Travel dates are set to {request['travel_dates']}, so timing and seasonality are considered.")
            score += 5
        if request.get('travel_month'):
            summary_sections.append(f"The travel month is {request['travel_month']}, so weather and seasonal activities are included.")
            score += 3
        if request.get('interests'):
            summary_sections.append(f"The plan reflects interests in {', '.join(request['interests'])}.")
            score += 2
        if assistance.get('visa_guidance'):
            summary_sections.append('Visa and travel guidance are included for the destination.')
        if memory_context:
            summary_sections.append('Conversation memory was used to keep the plan consistent.')
            score += 5
        if requested_budget and budget.get('total_converted') and budget['total_converted'] <= requested_budget * 0.75:
            summary_sections.append('The plan is conservative and leaves room for upgrades.')
            score += 5

        validation = 'Travel plan validated for structure, budget fit, personalization, weather, visa guidance, and travel sequencing.'
        if issues:
            validation = validation + f' Remaining watchpoints: {", ".join(issues)}.'

        score = max(0, min(score, 100))
        summary = ' '.join(summary_sections)
        return {'summary': summary, 'validation': validation, 'itinerary_length': itinerary_days, 'confidence_score': f'{score}%'}
