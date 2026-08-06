from typing import Dict, List, Optional
from tools.visa_lookup import lookup_visa_info
from tools.weather_service import get_weather_forecast


class TravelAssistanceAgent:
    def provide(
        self,
        destination: str,
        travel_dates: Optional[str],
        nationality: Optional[str],
        interests: Optional[List[str]] = None,
        budget: Optional[float] = None,
        travelers: Optional[int] = None,
        preferred_transportation: Optional[str] = None,
        preferred_accommodation: Optional[str] = None,
        travel_season: Optional[str] = None,
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
            'packing_tips': self._build_packing_tips(weather['forecast'], travel_season),
            'emergency_numbers': self._emergency_numbers(normalized_destination),
            'currency': self._currency(normalized_destination),
            'language': self._language(normalized_destination),
            'time_zone': self._time_zone(normalized_destination),
            'power_plug': self._power_plug(normalized_destination),
            'local_transport': self._local_transport(normalized_destination, preferred_transportation),
            'safety_tips': self._safety_tips(normalized_destination),
            'food_recommendations': self._food_recommendations(destination, interests or []),
            'packing_checklist': self._build_packing_checklist(weather['forecast'], travel_season),
            'travel_tips': self._travel_tips(destination, travel_season, preferred_accommodation),
            'must_visit': self._must_visit(destination),
        }

    def _build_packing_tips(self, forecast: str, travel_season: Optional[str]) -> str:
        tips = ['Pack comfortable walking shoes.', 'Carry a reusable water bottle.']
        if 'chilly' in forecast.lower() or 'cool' in forecast.lower() or travel_season in {'winter', 'autumn'}:
            tips.append('Bring a warm jacket or sweater for cooler evenings.')
        if 'rain' in forecast.lower() or travel_season == 'monsoon':
            tips.append('Pack a compact raincoat or umbrella.')
        if 'sunny' in forecast.lower() or 'warm' in forecast.lower() or travel_season in {'summer', 'spring'}:
            tips.append('Pack sunscreen and a hat for daytime activities.')
        return ' '.join(tips)

    def _build_packing_checklist(self, forecast: str, travel_season: Optional[str]) -> str:
        items = ['Passport and ID', 'Phone charger and power bank', 'Medications', 'Comfortable walking shoes']
        if 'rain' in forecast.lower() or travel_season == 'monsoon':
            items.append('Umbrella or rain jacket')
        if 'cool' in forecast.lower() or travel_season in {'winter', 'autumn'}:
            items.append('Light jacket')
        return ', '.join(items)

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
        mapping = {'Japan': 'Police: 110, Ambulance: 119', 'France': 'Police: 17, Ambulance: 15', 'Indonesia': 'Police: 110, Ambulance: 118 or 119', 'United States': 'Police/Fire/Ambulance: 911', 'UAE': 'Police: 999, Ambulance: 998', 'India': 'Police: 100, Ambulance: 102'}
        return mapping.get(destination, 'Check local emergency services for the destination.')

    def _currency(self, destination: str) -> str:
        mapping = {'Japan': 'Japanese Yen (JPY)', 'France': 'Euro (EUR)', 'Indonesia': 'US Dollar (USD)', 'United States': 'US Dollar (USD)', 'UAE': 'United Arab Emirates Dirham (AED)', 'India': 'Indian Rupee (INR)'}
        key = destination.split(',')[0].strip()
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Local currency varies by country.')

    def _language(self, destination: str) -> str:
        mapping = {'Japan': 'Japanese', 'France': 'French', 'Indonesia': 'Indonesian', 'United States': 'English', 'UAE': 'Arabic, English widely spoken', 'India': 'Hindi and many regional languages'}
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Local language varies by country.')

    def _time_zone(self, destination: str) -> str:
        mapping = {'Japan': 'UTC +9', 'France': 'UTC +1', 'Indonesia': 'UTC +8', 'United States': 'UTC -5 to -8 depending on coast', 'UAE': 'UTC +4', 'India': 'UTC +5:30'}
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Check the local time zone for this destination.')

    def _power_plug(self, destination: str) -> str:
        mapping = {'Japan': 'Type A / B, 100V', 'France': 'Type C / E, 230V', 'Indonesia': 'Type C / F, 230V', 'United States': 'Type A / B, 120V', 'UAE': 'Type G, 230V', 'India': 'Type C / D / M, 230V'}
        key = destination
        if key.endswith('USA'):
            key = 'United States'
        return mapping.get(key, 'Bring a universal adapter and check voltage requirements.')

    def _local_transport(self, destination: str, preferred_transportation: Optional[str]) -> str:
        if preferred_transportation == 'car':
            return 'A rental car or private driver is practical for flexible sightseeing.'
        if preferred_transportation == 'train':
            return 'Use trains or local rail connections where available and reserve ahead.'
        return f'Use taxis, ride-hailing, and local public transport for {destination} depending on your route.'

    def _safety_tips(self, destination: str) -> str:
        return 'Keep copies of your documents, stay alert in crowded areas, and follow local advice.'

    def _food_recommendations(self, destination: str, interests: List[str]) -> str:
        if 'food' in interests:
            return f'Try local signature dishes and a food tour in {destination}.'
        return f'Sample local specialities and one market dining experience in {destination}.'

    def _travel_tips(self, destination: str, travel_season: Optional[str], preferred_accommodation: Optional[str]) -> str:
        base = f'Book your stay early for {destination} and keep your plan flexible around weather.'
        if travel_season:
            base += f' Adjust for {travel_season} travel conditions.'
        if preferred_accommodation == 'budget':
            base += ' Choose a central stay to avoid paying for long transfers.'
        return base

    def _must_visit(self, destination: str) -> str:
        return f'Check the signature attractions and one lesser-known spot in {destination} for a more balanced trip.'
