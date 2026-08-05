from typing import Dict, Optional

VISA_RULES: Dict[str, Dict[str, str]] = {
    'Japan': {
        'visa': 'Tourist visa required for most nationalities. Apply through the nearest embassy or consulate.',
        'notes': 'Visa processing typically takes 5-10 business days.',
    },
    'France': {
        'visa': 'Schengen visa required for non-EU travelers. Apply 15 days before travel.',
        'notes': 'Carry proof of accommodation and travel insurance.',
    },
    'Indonesia': {
        'visa': 'Visa on arrival available for many nationalities. 30-day stay permitted.',
        'notes': 'Ensure passport validity is at least 6 months.',
    },
    'United States': {
        'visa': 'Nonimmigrant B-2 tourist visa required. Book an interview at the US consulate.',
        'notes': 'Processing can take several weeks.',
    },
    'UAE': {
        'visa': 'Visa-free entry or visa on arrival for many countries. Confirm with local authorities.',
        'notes': 'Travel duration depends on nationality.',
    },
    'India': {
        'visa': 'Domestic travel does not require a visa. Carry valid government ID.',
        'notes': 'For international visitors, e-Visa is available for select nationalities.',
    },
}

CITY_TO_COUNTRY = {
    'Tokyo': 'Japan',
    'Paris': 'France',
    'Bali': 'Indonesia',
    'New York': 'United States',
    'Dubai': 'UAE',
    'Goa': 'India',
}

def lookup_visa_info(destination: str, nationality: Optional[str] = None) -> Dict[str, str]:
    normalized = destination.split(',')[0].strip()
    if normalized in CITY_TO_COUNTRY:
        normalized = CITY_TO_COUNTRY[normalized]
    if normalized.endswith('USA'):
        normalized = 'United States'
    entry = VISA_RULES.get(normalized)
    if entry:
        return {
            'destination': destination,
            'visa': entry['visa'],
            'notes': entry['notes'],
        }

    return {
        'destination': destination,
        'visa': 'Visa requirements vary by nationality. Verify with the official embassy website.',
        'notes': 'Always check the latest visa and travel advisory updates before departure.',
    }
