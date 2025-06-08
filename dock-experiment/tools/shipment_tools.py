from ..services import node_api_service
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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

def book_shipment_order(
    origin_city: str, origin_state: str, origin_zip: str,
    destination_city: str, destination_state: str, destination_zip: str,
    trailer_type: str,
    vehicle_year: int, vehicle_make: str, vehicle_model: str, vehicle_type: str,
    available_date: str,
    offer_price: float,
    total_price: float,
    cod_amount: float,
    cod_payment_method: str,
    cod_payment_location: str,
    origin_address1: str,
    destination_address1: str,
    is_inoperable: bool = False,
    origin_address2: Optional[str] = "",
    destination_address2: Optional[str] = "",
    origin_phone: Optional[str] = "N/A",
    destination_phone: Optional[str] = "N/A",
    origin_location_type: Optional[str] = "Residence",
    destination_location_type: Optional[str] = "Residence",
    origin_forklift: bool = False,
    destination_forklift: bool = False,
    pickup_instructions: Optional[str] = "",
    save_contact: bool = False,
    vehicle_qty: int = 1
) -> dict:
    """
    Creates a new shipment booking order for the logged-in user. 
    This should be called after a user agrees to a quote.
    """
    logger.info(f"Tool: book_shipment_order called for {vehicle_year} {vehicle_make} {vehicle_model}.")
    
    payload = {
        "origin": {
            "city": origin_city,
            "state": origin_state,
            "zip": origin_zip,
            "adrress1": origin_address1,
            "adrress2": origin_address2,
            "phone": origin_phone,
            "LocationType": origin_location_type,
            "forklift": origin_forklift
        },
        "destination": {
            "city": destination_city,
            "state": destination_state,
            "zip": destination_zip,
            "adrress1": destination_address1,
            "adrress2": destination_address2,
            "phone": destination_phone,
            "LocationType": destination_location_type,
            "forklift": destination_forklift
        },
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
        "PickupInstructions": pickup_instructions,
        "offerPrice": offer_price,
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

    logger.debug(f"Submitting booking payload: {payload}")
    return node_api_service.create_trucking_order(payload) 