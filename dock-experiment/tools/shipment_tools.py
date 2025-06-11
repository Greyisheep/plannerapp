from ..services import node_api_service
import logging
from typing import Optional

logger = logging.getLogger(__name__)

STATE_ABBREVIATIONS = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID', 
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS', 
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD', 
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK', 
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 
    'wisconsin': 'WI', 'wyoming': 'WY'
}

def _get_state_abbr(state_name: str) -> str:
    """Converts a full state name to its 2-letter abbreviation, case-insensitively."""
    return STATE_ABBREVIATIONS.get(state_name.lower(), state_name)

def search_user_shipments(search_query: Optional[str] = None) -> dict:
    """Searches a logged-in user's shipments. A search query can be provided to filter results."""
    logger.info(f"Tool: search_user_shipments called with query: '{search_query}'.")
    # This simplified tool uses the basic /api/trucking search.
    # The agent can be taught to use the more advanced one if needed.
    return node_api_service.search_trucking_orders(search_query=search_query)

def search_user_bookings_advanced(
    search_query: Optional[str] = None,
    type_vehicle: Optional[str] = None,
    type_shipping: Optional[str] = None,
    is_completed: Optional[bool] = None
) -> dict:
    """Performs an advanced search on a user's bookings with multiple optional filters."""
    logger.info(f"Tool: search_user_bookings_advanced called with query: '{search_query}', type_vehicle: '{type_vehicle}', type_shipping: '{type_shipping}', is_completed: {is_completed}")
    return node_api_service.search_bookings(
        search_query=search_query,
        type_vehicle=type_vehicle,
        type_shipping=type_shipping,
        done=is_completed
    )

def create_trucking_shipment(
    origin_city: str, origin_state: str, origin_zip: str,
    destination_city: str, destination_state: str, destination_zip: str,
    trailer_type: str,
    vehicle_year: int, vehicle_make: str, vehicle_model: str,
    available_date: str, # Format: "YYYY-MM-DD"
    offer_price: float,
    total_price: float,
    cod_amount: float,
    vehicle_type: str = "SUV", # Default to 'SUV' if not provided
    cod_payment_method: str = "CASH_CERTIFIED_FUNDS",
    cod_payment_location: str = "Delivery",
    origin_address1: Optional[str] = None,
    destination_address1: Optional[str] = None,
    is_inoperable: bool = False,
    origin_address2: Optional[str] = None,
    destination_address2: Optional[str] = None,
    origin_phone: Optional[str] = None,
    destination_phone: Optional[str] = None,
    origin_location_type: Optional[str] = None,
    destination_location_type: Optional[str] = None,
    origin_forklift: bool = False,
    destination_forklift: bool = False,
    pickup_instructions: Optional[str] = None,
    save_contact: bool = False,
    vehicle_qty: int = 1
) -> dict:
    """
    Creates a new trucking shipment. This is used to book a vehicle transport.
    The agent should guide the user to collect all necessary information.
    If a user provides a ZIP code, use the 'get_location_from_zip' tool to get city and state.
    """
    logger.info(f"Tool: create_trucking_shipment called for {vehicle_year} {vehicle_make} {vehicle_model}.")

    origin_state_abbr = _get_state_abbr(origin_state)
    destination_state_abbr = _get_state_abbr(destination_state)

    origin = {
        "city": origin_city,
        "state": origin_state_abbr,
        "zip": origin_zip,
        "forklift": origin_forklift
    }
    if origin_address1:
        origin["address1"] = origin_address1
    if origin_address2:
        origin["address2"] = origin_address2
    if origin_phone:
        origin["phone"] = origin_phone
    if origin_location_type:
        origin["LocationType"] = origin_location_type

    destination = {
        "city": destination_city,
        "state": destination_state_abbr,
        "zip": destination_zip,
        "forklift": destination_forklift
    }
    if destination_address1:
        destination["address1"] = destination_address1
    if destination_address2:
        destination["address2"] = destination_address2
    if destination_phone:
        destination["phone"] = destination_phone
    if destination_location_type:
        destination["LocationType"] = destination_location_type
    
    payload = {
        "origin": origin,
        "destination": destination,
        "trailerType": trailer_type,
        "vehicles": [
            {
                "year": vehicle_year,
                "make": vehicle_make,
                "model": vehicle_model,
                "vehicleType": vehicle_type,
                "qty": vehicle_qty
            }
        ],
        "availableDate": available_date, # "YYYY-MM-DD"
        "hasInOpvehicle": is_inoperable,
        "saveContact": save_contact,
        "price": {
            "total": total_price,
            "cod": {
                "amount": cod_amount,
                "paymentMethod": cod_payment_method, # e.g., "CASH_CERTIFIED_FUNDS"
                "paymentLocation": cod_payment_location # e.g., "Delivery"
            }
        }
    }
    if pickup_instructions:
        payload["PickupInstructions"] = pickup_instructions

    logger.debug(f"Submitting booking payload: {payload}")
    return node_api_service.create_trucking_order(payload) 