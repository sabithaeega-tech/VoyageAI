from typing import Any, Dict, List, Optional

DESTINATIONS = [
    {
        'name': 'Tokyo, Japan',
        'region': 'Asia',
        'tags': ['culture', 'food', 'city', 'technology'],
        'avg_daily_cost': 22000,
        'visa_required': True,
        'currency': 'JPY',
        'attractions': ['Senso-ji Temple', 'Shibuya Crossing', 'Tsukiji Outer Market', 'Akihabara'],
    },
    {
        'name': 'Paris, France',
        'region': 'Europe',
        'tags': ['culture', 'romance', 'art', 'city'],
        'avg_daily_cost': 320,
        'visa_required': True,
        'currency': 'EUR',
        'attractions': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame Cathedral', 'Montmartre'],
    },
    {
        'name': 'Bali, Indonesia',
        'region': 'Asia',
        'tags': ['beach', 'relaxation', 'nature', 'spa'],
        'avg_daily_cost': 180,
        'visa_required': False,
        'currency': 'USD',
        'attractions': ['Ubud Rice Terraces', 'Kuta Beach', 'Tanah Lot Temple', 'Seminyak Beach Club'],
    },
    {
        'name': 'New York, USA',
        'region': 'North America',
        'tags': ['city', 'shopping', 'culture', 'food'],
        'avg_daily_cost': 320,
        'visa_required': True,
        'currency': 'USD',
        'attractions': ['Central Park', 'Statue of Liberty', 'Times Square', 'Metropolitan Museum of Art'],
    },
    {
        'name': 'Dubai, UAE',
        'region': 'Middle East',
        'tags': ['luxury', 'shopping', 'architecture', 'desert'],
        'avg_daily_cost': 600,
        'visa_required': False,
        'currency': 'AED',
        'attractions': ['Burj Khalifa', 'Dubai Mall', 'Palm Jumeirah', 'Desert Safari'],
    },
    {
        'name': 'Goa, India',
        'region': 'Asia',
        'tags': ['beach', 'party', 'relaxation', 'culture'],
        'avg_daily_cost': 9500,
        'visa_required': False,
        'currency': 'INR',
        'attractions': ['Baga Beach', 'Anjuna Flea Market', 'Old Goa Churches', 'Dudhsagar Falls'],
    },
]

INTEREST_MAP = {
    'culture': ['culture', 'history', 'museums', 'art'],
    'beach': ['beach', 'relaxation', 'sun', 'surf'],
    'nature': ['nature', 'hiking', 'wildlife', 'waterfall'],
    'food': ['food', 'cuisine', 'dining', 'restaurants'],
    'city': ['city', 'urban', 'shopping', 'nightlife'],
    'adventure': ['adventure', 'trekking', 'rafting', 'sports'],
    'luxury': ['luxury', 'premium', 'spa', 'exclusive'],
}

BEST_MONTHS = {
    'Tokyo': 'October–November',
    'Paris': 'October–November',
    'Bali': 'April–May, September–November',
    'New York': 'September–October',
    'Dubai': 'October–March',
    'Goa': 'November–February',
}

WEATHER_SUMMARIES = {
    'Tokyo': 'Cool and crisp with autumn colors in November.',
    'Paris': 'Chilly, with a chance of rain and cozy cafés.',
    'Bali': 'Warm and tropical with occasional rain showers.',
    'New York': 'Mild autumn days and cooler evenings.',
    'Dubai': 'Sunny, dry and warm with clear skies.',
    'Goa': 'Warm beach weather and pleasant evenings.',
}

VISA_SUMMARIES = {
    True: 'Tourist visa required; allow time for processing.',
    False: 'Visa-free or visa on arrival for many travelers.',
}

def _normalize_destination_name(destination: str) -> str:
    return destination.split(',')[0].strip()

def _build_recommendation_metadata(
    destination: Dict[str, Any],
    interests: List[str],
    budget: float,
    duration: int,
) -> Dict[str, Any]:
    normalized = _normalize_destination_name(destination['name'])
    reasons = []
    interest_labels = [interest.capitalize() for interest in interests if interest]
    if interest_labels:
        reasons.append(f"Matches interests in {', '.join(interest_labels)}.")

    if any(tag in interests for tag in destination['tags']):
        matching_tags = [tag for tag in destination['tags'] if tag in interests]
        if matching_tags:
            reasons.append(f"Strong match for {', '.join(matching_tags)} experiences.")

    if duration >= 5:
        reasons.append('Good fit for a 5+ day itinerary with strong local experiences.')
    else:
        reasons.append('Suitable for a compact trip with top highlights.')

    cost_estimate = destination['avg_daily_cost'] * duration
    if budget and cost_estimate <= budget:
        reasons.append('Fits your stated budget range for a comfortable stay.')
    else:
        reasons.append('May require budget adjustment for premium experiences.')

    return {
        **destination,
        'reason': ' '.join(reasons),
        'weather': WEATHER_SUMMARIES.get(normalized, 'Expect variable local weather. Check closer to travel dates.'),
        'best_months': BEST_MONTHS.get(normalized, 'All year'),
        'visa': VISA_SUMMARIES[destination['visa_required']],
        'recommendation_points': reasons,
    }


def search_destinations(
    interests: List[str],
    budget: Optional[float],
    duration: Optional[int],
    preferred_region: Optional[str] = None,
) -> List[Dict[str, Any]]:
    budget = budget or 0
    duration = duration or 5
    preferred_region = (preferred_region or '').strip().lower()
    matched: List[Dict[str, Any]] = []

    interest_tokens = set()
    for interest in interests:
        interest_tokens.add(interest.lower())
        interest_tokens.update(INTEREST_MAP.get(interest.lower(), []))

    for destination in DESTINATIONS:
        region_match = not preferred_region or preferred_region in destination['region'].lower()
        if not region_match:
            continue

        tag_match = any(tag in interest_tokens for tag in destination['tags']) if interest_tokens else True
        cost_safe = destination['avg_daily_cost'] * duration * 1.1 <= max(budget, destination['avg_daily_cost'] * duration * 3)

        if tag_match and cost_safe:
            matched.append(_build_recommendation_metadata(destination, interests, budget, duration))

    if not matched:
        matched = [_build_recommendation_metadata(destination, interests, budget, duration) for destination in sorted(DESTINATIONS, key=lambda item: item['avg_daily_cost'])]

    return matched
