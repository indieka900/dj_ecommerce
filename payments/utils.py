import time
from decimal import Decimal
import requests

# Cache variables
exchange_rate_cache = None
last_fetched_time = 0
CACHE_DURATION = 3600 * 6 

def fetch_exchange_rate():
    """Fetches the exchange rate from the API."""
    global exchange_rate_cache, last_fetched_time
    response = requests.get("https://api.exchangerate-api.com/v4/latest/KES")
    data = response.json()
    exchange_rate_cache = Decimal(data["rates"]["USD"])
    last_fetched_time = time.time()

def convert_kes_to_usd(amount_in_kes):
    """Converts KES to USD using a cached exchange rate."""
    global exchange_rate_cache, last_fetched_time
    # Refresh the exchange rate if it's not cached or expired
    if exchange_rate_cache is None or (time.time() - last_fetched_time > CACHE_DURATION):
        fetch_exchange_rate()
    
    amount_in_usd = Decimal(amount_in_kes) * exchange_rate_cache
    return f"{amount_in_usd:.2f}"

def format_phone_number(phone_number):
    """
    Format phone number to start with 254 and be 12 digits long.
    Examples:
        0712345678 -> 254712345678
        +254712345678 -> 254712345678
        712345678 -> 254712345678
    """
    # Remove any spaces, hyphens or plus signs
    phone = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    
    # If number starts with 0, remove it
    if phone.startswith('0'):
        phone = phone[1:]
    
    # If number starts with 254, use it as is
    if phone.startswith('254'):
        phone = phone
    # Otherwise, add 254 prefix
    else:
        phone = f"254{phone}"
    
    # Verify the length
    if len(phone) != 12:
        raise ValueError("Phone number must be 9 digits after the prefix")
        
    return phone