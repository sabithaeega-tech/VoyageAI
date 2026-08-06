import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.itinerary_agent import ItineraryPlannerAgent


class ItineraryPlannerAgentTests(unittest.TestCase):
    def test_fallback_itinerary_uses_destination_specific_places_and_stay(self):
        agent = ItineraryPlannerAgent()
        destination = {
            'name': 'Tokyo, Japan',
            'tags': ['culture', 'food', 'city'],
            'attractions': ['Senso-ji Temple', 'Shibuya Crossing', 'Tsukiji Outer Market'],
            'currency': 'JPY',
        }

        itinerary = agent._build_fallback_itinerary(
            destination=destination,
            duration=3,
            interests=['culture', 'food'],
            travel_month='November',
            accommodation_style='moderate',
            budget=120000,
            start_day=1,
        )

        self.assertEqual(len(itinerary), 3)
        self.assertTrue(all('places_to_visit' in day for day in itinerary))
        self.assertTrue(all('stay' in day for day in itinerary))
        self.assertTrue(any('Senso-ji Temple' in place for day in itinerary for place in day['places_to_visit']))
        self.assertTrue(any('Tokyo, Japan' in day['stay'] for day in itinerary))

    def test_parsed_itinerary_formats_list_and_dict_content_readably(self):
        agent = ItineraryPlannerAgent()
        response = '''[
            {
                "day": "Day 1",
                "morning": [{"activity": "Visit Mutianyu Great Wall", "duration": 4, "description": "Explore the ancient fortifications"}],
                "afternoon": [{"activity": "Visit Beijing Museum of Natural History", "duration": 3, "description": "Learn about China's natural wonders"}],
                "evening": [{"activity": "Dine at a rooftop restaurant", "duration": 3, "description": "Enjoy panoramic views"}],
                "places_to_visit": [{"name": "Mutianyu Great Wall", "type": "Attraction", "distance": 1}],
                "stay": {"type": "Budget Hotel", "rating": 4, "price": 800.0}
            }
        ]'''

        itinerary = agent._parse_response(response, duration=1, destination={'name': 'Beijing', 'tags': ['culture'], 'attractions': []}, interests=['culture'], travel_month='November', accommodation_style='moderate', budget=50000)

        self.assertEqual(len(itinerary), 1)
        self.assertIsInstance(itinerary[0]['morning'], str)
        self.assertIn('Visit Mutianyu Great Wall', itinerary[0]['morning'])
        self.assertIsInstance(itinerary[0]['afternoon'], str)
        self.assertIsInstance(itinerary[0]['evening'], str)
        self.assertIsInstance(itinerary[0]['places_to_visit'], list)
        self.assertTrue(any('Mutianyu Great Wall' in place for place in itinerary[0]['places_to_visit']))
        self.assertIsInstance(itinerary[0]['stay'], str)
        self.assertIn('Budget Hotel', itinerary[0]['stay'])

    def test_parsed_itinerary_extracts_specific_places_and_stay_from_activity_text(self):
        agent = ItineraryPlannerAgent()
        response = '''[
            {
                "day": "Day 1",
                "morning": "Check-in at Ubud Hotel",
                "afternoon": "Explore Ubud Monkey Forest and Ubud Art Market",
                "evening": "Sunset view at Campuhan Ridge Walk"
            }
        ]'''

        itinerary = agent._parse_response(response, duration=1, destination={'name': 'Bali', 'tags': ['culture', 'beach'], 'attractions': ['Ubud Rice Terraces', 'Kuta Beach']}, interests=['culture'], travel_month='November', accommodation_style='budget', budget=50000)

        self.assertEqual(len(itinerary), 1)
        places = itinerary[0]['places_to_visit']
        self.assertTrue(any('Ubud Monkey Forest' in place for place in places))
        self.assertTrue(any('Ubud Art Market' in place for place in places))
        self.assertTrue(any('Campuhan Ridge Walk' in place for place in places))
        self.assertIsInstance(itinerary[0]['stay'], str)
        self.assertIn('Ubud Monkey Forest', itinerary[0]['stay'])

    def test_fallback_itinerary_uses_destination_specific_places_for_kashmir(self):
        agent = ItineraryPlannerAgent()
        destination = {
            'name': 'Kashmir',
            'tags': ['food', 'nature', 'culture'],
            'attractions': [],
        }

        itinerary = agent._build_fallback_itinerary(
            destination=destination,
            duration=2,
            interests=['food', 'nature'],
            travel_month='summer',
            accommodation_style='budget',
            budget=50000,
            start_day=1,
        )

        self.assertEqual(len(itinerary), 2)
        self.assertTrue(any('Dal Lake' in place for place in itinerary[0]['places_to_visit']))
        self.assertTrue(any('Gulmarg' in place for place in itinerary[0]['places_to_visit']))
        self.assertIn('Dal Lake', itinerary[0]['stay'])


if __name__ == '__main__':
    unittest.main()
