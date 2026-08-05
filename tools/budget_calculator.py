from typing import Any, Dict

STYLE_MULTIPLIER = {
    'budget': 0.8,
    'moderate': 1.0,
    'premium': 1.4,
}

def estimate_trip_budget(
    destination: Dict[str, Any],
    duration: int,
    travelers: int = 1,
    accommodation_style: str = 'moderate',
) -> Dict[str, Any]:
    style_multiplier = STYLE_MULTIPLIER.get(accommodation_style.lower(), 1.0)
    base_cost = destination.get('avg_daily_cost', 150)
    # Compute a clearer breakdown including flights and shopping.
    daily_cost = base_cost * style_multiplier

    # Per-day components (per person)
    lodging_pct = 0.45
    food_pct = 0.20
    transport_pct = 0.10
    activities_pct = 0.15

    lodging_per_day = round(daily_cost * lodging_pct)
    food_per_day = round(daily_cost * food_pct)
    transport_per_day = round(daily_cost * transport_pct)
    activities_per_day = round(daily_cost * activities_pct)

    subtotal = (lodging_per_day + food_per_day + transport_per_day + activities_per_day) * duration * travelers

    # Estimate flights as a reasonable fraction of subtotal (varies by distance/origin; use 30%)
    flights = round(subtotal * 0.30)

    # Shopping / miscellaneous estimated as 8% of subtotal
    shopping = round(subtotal * 0.08)

    before_contingency = subtotal + flights + shopping
    contingency = round(before_contingency * 0.10)
    total = before_contingency + contingency

    breakdown = {
        'flights': flights,
        'accommodation': lodging_per_day * duration * travelers,
        'food': food_per_day * duration * travelers,
        'transport': transport_per_day * duration * travelers,
        'activities': activities_per_day * duration * travelers,
        'shopping': shopping,
        'contingency': contingency,
    }

    return {
        'destination': destination.get('name', 'Unknown'),
        'duration': duration,
        'travelers': travelers,
        'currency': destination.get('currency', 'USD'),
        'flights': flights,
        'lodging': breakdown['accommodation'],
        'food': breakdown['food'],
        'transport': breakdown['transport'],
        'activities': breakdown['activities'],
        'shopping': breakdown['shopping'],
        'contingency': breakdown['contingency'],
        'total': total,
        'accommodation_style': accommodation_style,
        'breakdown': breakdown,
    }
