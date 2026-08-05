from typing import Dict, Optional
from tools.visa_lookup import lookup_visa_info
from tools.weather_service import get_weather_forecast


class TravelAssistanceAgent:
    def provide(
        self,
        destination: str,
        travel_dates: Optional[str],
        nationality: Optional[str],
    ) -> Dict[str, str]:
        normalized_destination = self._normalize_destination(destination)
        visa = lookup_visa_info(normalized_destination, nationality)
        weather = get_weather_forecast(normalized_destination, travel_dates)

        return {
            'destination': destination,
            'travel_dates': travel_dates or 'Flexible',
            'nationality': nationality or 'Not specified',
            'visa_guidance': visa['visa'],
            'visa_notes': visa['notes'],
            'weather_forecast': weather['forecast'],
            'weather_month': weather['travel_month'],
            'packing_tips': self._build_packing_tips(weather['forecast']),
            'emergency_numbers': self._emergency_numbers(normalized_destination),
            'currency': self._currency(normalized_destination),
            'language': self._language(normalized_destination),
            'time_zone': self._time_zone(normalized_destination),
            'power_plug': self._power_plug(normalized_destination),
            'local_transport': self._local_transport(normalized_destination),
            'safety_tips': self._safety_tips(normalized_destination),
        }

    def _build_packing_tips(self, forecast: str) -> str:
        tips = ['Pack comfortable walking shoes.', 'Carry a reusable water bottle.']
        if 'chilly' in forecast.lower() or 'cool' in forecast.lower():
            tips.append('Bring a warm jacket or sweater for cooler evenings.')
        if 'rain' in forecast.lower() or 'rainy' in forecast.lower():
            tips.append('Pack a compact raincoat or umbrella.')
        if 'sunny' in forecast.lower() or 'warm' in forecast.lower():
            tips.append('Pack sunscreen and a hat for daytime activities.')
        return ' '.join(tips)

    def _normalize_destination(self, destination: str) -> str:
        key = destination.split(',')[-1].strip()
        if key.endswith('USA'):
            return 'United States'
        if key == 'Tokyo' or 'Japan' in destination:
            return 'Japan'
        if key == 'Paris' or 'France' in destination:
            return 'France'
        if key == 'Indonesia' or 'Bali' in destination:
            return 'Indonesia'
        if key == 'UAE' or 'Dubai' in destination:
            return 'UAE'
        if key == 'India' or 'Goa' in destination:
            return 'India'
        return key

    def _emergency_numbers(self, destination: str) -> str:
        mapping = {
            'Japan': 'Police: 110, Ambulance: 119',
            'France': 'Police: 17, Ambulance: 15',
            'Indonesia': 'Police: 110, Ambulance: 118 or 119',
            'United States': 'Police/Fire/Ambulance: 911',
            'UAE': 'Police: 999, Ambulance: 998',
            'India': 'Police: 100, Ambulance: 102',
        }
        return mapping.get(destination, 'Check local emergency services for the destination.')

    def _currency(self, destination: str) -> str:
        mapping = {
            'Japan': 'Japanese Yen (JPY)',
            'France': 'Euro (EUR)',
            'Indonesia': 'US Dollar (USD)',
            'United States': 'US Dollar (USD)',
            'UAE': 'United Arab Emirates Dirham (AED)',
            'India': 'Indian Rupee (INR)',
        }
        key = destination.split(',')[0].strip()
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Local currency varies by country.')

    def _language(self, destination: str) -> str:
        mapping = {
            'Japan': 'Japanese',
            'France': 'French',
            'Indonesia': 'Indonesian',
            'United States': 'English',
            'UAE': 'Arabic, English widely spoken',
            'India': 'Hindi and many regional languages',
        }
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Local language varies by country.')

    def _time_zone(self, destination: str) -> str:
        mapping = {
            'Japan': 'UTC +9',
            'France': 'UTC +1',
            'Indonesia': 'UTC +8',
            'United States': 'UTC -5 to -8 depending on coast',
            'UAE': 'UTC +4',
            'India': 'UTC +5:30',
        }
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Check the local time zone for this destination.')

    def _power_plug(self, destination: str) -> str:
        mapping = {
            'Japan': 'Type A / B, 100V',
            'France': 'Type C / E, 230V',
            'Indonesia': 'Type C / F, 230V',
            'United States': 'Type A / B, 120V',
            'UAE': 'Type G, 230V',
            'India': 'Type C / D / M, 230V',
        }
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Bring a universal adapter and check voltage requirements.')

    def _local_transport(self, destination: str) -> str:
        mapping = {
            'Japan': 'Excellent public transport: trains, metro, buses, and taxis.',
            'France': 'Strong rail network, metro in cities, and ride-hailing available.',
            'Indonesia': 'Local taxis, ride-hailing, and island transfers by boat.',
            'United States': 'Ride-hailing, subways in major cities, and car rentals.',
            'UAE': 'Metro, taxis, and ride-hailing are widely available.',
            'India': 'Local trains, taxis, autos, and ride-hailing services.',
        }
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Local transportation options vary by destination.')

    def _safety_tips(self, destination: str) -> str:
        mapping = {
            'Japan': 'Stay aware of local etiquette, keep valuables secure, and use public transport.',
            'France': 'Watch for pickpockets in tourist areas and carry a copy of your documents.',
            'Indonesia': 'Use bottled water, stay sun-safe, and follow local travel advice.',
            'United States': 'Stay aware of busy city streets and follow local safety guidelines.',
            'UAE': 'Respect local customs and dress codes, especially in public areas.',
            'India': 'Be mindful of traffic, stay hydrated, and keep personal items secure.',
        }
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Follow general travel safety best practices and local guidance.')
