import pgeocode
from typing import Optional, Dict, Any

# Initialize the geocoder for the US
nomi = pgeocode.Nominatim('us')

def get_location_from_zip(zip_code: str) -> Optional[Dict[str, Any]]:
    """
    Looks up the city and state for a given US ZIP code using the pgeocode library.
    This function works offline and does not require an API key.
    """
    try:
        query_result = nomi.query_postal_code(zip_code)

        # pgeocode returns NaN for fields it can't find. We need to check for that.
        if query_result.empty or not isinstance(query_result.place_name, str):
            return None

        return {
            "city": query_result.place_name,
            "state": query_result.state_name,
            "zip": query_result.postal_code
        }
    except Exception as e:
        print(f"Error looking up zip code with pgeocode: {e}")
        return None 