from datetime import datetime
from typing import Dict, Optional

WEATHER_PATTERNS: Dict[str, str] = {
    'Japan': 'Cool and crisp with autumn colors in November. Expect mild days and cooler evenings.',
    'France': 'Late autumn with chilly, rainy weather in November. Pack layers and a raincoat.',
    'Indonesia': 'Warm tropical weather with some humidity. Light clothing and sunscreen are advised.',
    'United States': 'Variable weather in November; city centers can be cool, with mild days and colder nights.',
    'UAE': 'Warm and dry with sunny skies. Ideal for desert experiences and city sightseeing.',
    'India': 'Warm and pleasant weather in many regions. Great for beach and cultural travel.',
}

CITY_TO_COUNTRY = {
    'Tokyo': 'Japan',
    'Paris': 'France',
    'Bali': 'Indonesia',
    'New York': 'United States',
    'Dubai': 'UAE',
    'Goa': 'India',
}

def get_weather_forecast(destination: str, travel_date: Optional[str] = None) -> Dict[str, str]:
    month = 'unknown'
    if travel_date:
        try:
            month = datetime.strptime(travel_date, '%Y-%m-%d').strftime('%B')
        except ValueError:
            pass

    normalized = destination.split(',')[0].strip()
    if normalized in CITY_TO_COUNTRY:
        normalized = CITY_TO_COUNTRY[normalized]
    if normalized.endswith('USA'):
        normalized = 'United States'

    forecast = WEATHER_PATTERNS.get(normalized, 'Expect variable local weather. Check a local forecast closer to your travel date.')
    return {
        'destination': destination,
        'travel_month': month,
        'forecast': forecast,
    }
