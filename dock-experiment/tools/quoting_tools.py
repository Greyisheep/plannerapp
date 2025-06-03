from ..services import node_api_service
import logging

logger = logging.getLogger(__name__)

def get_trucking_price_quote(
    pickup_city: str, pickup_state: str, pickup_zip: str, pickup_country: str,
    delivery_city: str, delivery_state: str, delivery_zip: str, delivery_country: str,
    vehicle_year: str, vehicle_make: str, vehicle_model: str, 
    vehicle_type: str = "SUV", # Default or ask, ensure this matches API expectations or is derived
    vehicle_operable: bool = True,
    # Optional user details - decide if these should come from ADK session or be fixed for now
    user_ip: str = "127.0.0.1", # Placeholder, ideally fetched dynamically if needed by API
    user_firstname: str = "DockMind",
    user_lastname: str = "User",
    user_email: str = "quote@dockmind.ai",
    user_country: str = "USA", # This seems to be a general user country in the API spec
    user_state: str = "CA",   # General user state
    user_city: str = "Anytown" # General user city
) -> dict:
    """Gets a trucking price quote by providing pickup, delivery, and vehicle details."""
    logger.info(f"Tool: get_trucking_price_quote called with: PU: {pickup_city}/{pickup_zip}, Del: {delivery_city}/{delivery_zip}, Veh: {vehicle_year} {vehicle_make} {vehicle_model}")

    # Validate required string parameters
    required_strings = {
        "pickup_city": pickup_city, "pickup_state": pickup_state, "pickup_zip": pickup_zip, "pickup_country": pickup_country,
        "delivery_city": delivery_city, "delivery_state": delivery_state, "delivery_zip": delivery_zip, "delivery_country": delivery_country,
        "vehicle_year": vehicle_year, "vehicle_make": vehicle_make, "vehicle_model": vehicle_model, "vehicle_type": vehicle_type
    }
    for name, val in required_strings.items():
        if not val or not isinstance(val, str):
            logger.error(f"Invalid or missing string value for '{name}' in get_trucking_price_quote")
            return {"error": True, "message": f"Missing or invalid value for {name}."}
    
    if not isinstance(vehicle_operable, bool):
        logger.error(f"Invalid value for 'vehicle_operable', must be boolean.")
        return {"error": True, "message": "Invalid value for vehicle_operable, must be true or false."}

    # The API spec for "offerPrice" and the top-level user geo fields (country, state, city) vs stopNumber fields is a bit ambiguous.
    # Assuming top-level country, state, city are for the user/requester, and stopNumber details are specific to pickup/delivery.
    payload = {
        "Ip": user_ip, 
        "firstname": user_firstname,
        "lastname": user_lastname,
        "email": user_email,
        "country": user_country, 
        "state": user_state,   
        "city": user_city,    
        "offerPrice": "0", # Per API spec, seems to be a fixed string "0" or needs clarification
        "stopNumber1": {
            "city": pickup_city,
            "state": pickup_state,
            "country": pickup_country,
            "code": pickup_zip
            # "streetAddress1": "123 Pickup St", # Street address was commented out in API spec example
        },
        "stopNumber2": {
            "city": delivery_city,
            "state": delivery_state,
            "country": delivery_country,
            "code": delivery_zip
            # "streetAddress1": "456 Delivery Ave", # Street address was commented out in API spec example
        },
        "vehicles": [
            {
                "year": vehicle_year,
                "make": vehicle_make,
                "model": vehicle_model,
                "vehicleType": vehicle_type, # e.g., "SUV"
                "operable": vehicle_operable,
                "pickUpStopNumber": 1, # Fixed as per API structure
                "dropOffStopNumber": 2 # Fixed as per API structure
            }
        ]
        # "enclosed": True, # Optional field from API spec example
        # "limit": 4      # Optional field from API spec example
    }
    
    logger.debug(f"Submitting quote payload: {payload}")
    result = node_api_service.submit_for_quote(payload)
    if result.get("error"):
        logger.error(f"API error in submit_for_quote: {result.get('message')}")
    elif not result.get("quote"):
        logger.warning(f"submit_for_quote API response did not contain a 'quote' ID. Response: {result}")
        # It might be good to return an error or a specific message if the quote ID is missing but no explicit API error occurred.
        # For now, returning the result as is for the agent to interpret.

    return result

def get_quote_details_by_id(quote_id: str) -> dict:
    """Fetches the full details of a previously generated quote using its unique quote ID."""
    logger.info(f"Tool: get_quote_details_by_id called for quote_id: {quote_id}")
    if not quote_id or not isinstance(quote_id, str):
        logger.error("Invalid quote_id provided to get_quote_details_by_id.")
        return {"error": True, "message": "Invalid quote_id provided."}
    result = node_api_service.fetch_quote_details(quote_id)
    if result.get("error"):
        logger.error(f"API error fetching quote details for ID {quote_id}: {result.get('message')}")
    return result 