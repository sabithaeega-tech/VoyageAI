from typing import Dict

EXCHANGE_RATES: Dict[str, float] = {
    'USD': 1.0,
    'INR': 83.0,
    'EUR': 0.92,
    'JPY': 151.0,
    'AED': 3.67,
    'GBP': 0.79,
}

def convert(amount: float, from_currency: str, to_currency: str) -> float:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        raise ValueError('Unsupported currency')
    usd_amount = amount / EXCHANGE_RATES[from_currency]
    total = round(usd_amount * EXCHANGE_RATES[to_currency], 2)
    return total
