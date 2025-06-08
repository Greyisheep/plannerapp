import requests
import os
import logging
import json

logger = logging.getLogger(__name__)

# --- Authentication State ---
# This is a simple in-memory store for the auth token.
# In a real-world multi-user scenario, this would be handled by a more robust session management system.
AUTH_TOKEN = None

# Attempt to get API_BASE_URL from environment variable, otherwise use a default
API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    logger.warning("API_BASE_URL not found in environment variables. Using default: https://dockporter.vercel.app/api")
    API_BASE_URL = "https://dockporter.vercel.app/api" # Default if not set

# Standard headers for JSON content type
COMMON_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def _get_auth_headers():
    """Helper to get headers, including auth if available."""
    headers = COMMON_HEADERS.copy()
    if AUTH_TOKEN:
        # Per the workaround, the token is sent directly without the "Bearer" prefix.
        headers["Authorization"] = AUTH_TOKEN
    return headers

def _handle_response(response: requests.Response, endpoint_name: str):
    """Helper function to handle API responses."""
    try:
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        # Check if response content is not empty before trying to parse JSON
        if response.content:
            return response.json()
        else:
            # Handle empty successful responses if applicable, or treat as an issue
            logger.warning(f"Empty response from {endpoint_name} with status {response.status_code}")
            return {"error": True, "message": f"Empty response from API for {endpoint_name}.", "status_code": response.status_code}
            
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred calling {endpoint_name}: {http_err} - Response: {response.text}")
        try:
            # Try to parse error response if it's JSON
            error_details = response.json()
        except json.JSONDecodeError:
            error_details = response.text
        return {"error": True, "message": f"API request failed for {endpoint_name}: {http_err}", "details": error_details, "status_code": response.status_code}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred calling {endpoint_name}: {req_err}")
        return {"error": True, "message": f"Request failed for {endpoint_name}: {req_err}"}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from {endpoint_name}: {json_err} - Response: {response.text}")
        return {"error": True, "message": f"Invalid JSON response from API for {endpoint_name}.", "details": response.text}


def login(email: str, password: str) -> dict:
    """Calls the Node.js API to log in a user and stores the auth token."""
    global AUTH_TOKEN
    endpoint = f"{API_BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    logger.info(f"Calling API: POST {endpoint} for user login.")
    try:
        response = requests.post(endpoint, json=payload, headers=COMMON_HEADERS, timeout=15)
        result = _handle_response(response, "login")
        if not result.get("error") and result.get("_token"):
            AUTH_TOKEN = result["_token"]
            logger.info(f"Login successful. Auth token stored for user.")
            # Return a user-friendly message, excluding the token itself for security.
            return {"success": True, "message": "Login successful.", "user": result.get("user")}
        elif not result.get("error"):
            logger.warning(f"Login response did not contain a '_token'. Response: {result}")
            return {"error": True, "message": "Login successful, but no authentication token was received."}
        else:
            AUTH_TOKEN = None # Clear any previous token on failed login
            return result
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for login."}

def get_user_profile() -> dict:
    """Calls the Node.js API to get the current user's profile using the stored auth token."""
    if not AUTH_TOKEN:
        return {"error": True, "message": "You must be logged in to perform this action."}
    endpoint = f"{API_BASE_URL}/users/me"
    logger.info(f"Calling API: GET {endpoint} for user profile.")
    try:
        response = requests.get(endpoint, headers=_get_auth_headers(), timeout=10)
        return _handle_response(response, "get_user_profile")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for get_user_profile."}


def fetch_vehicle_specs(vin: str) -> dict:
    """Calls the Node.js API to get vehicle specifications by VIN."""
    endpoint = f"{API_BASE_URL}/function/vehicle"
    params = {"vin": vin}
    logger.info(f"Calling API: GET {endpoint} with VIN: {vin}")
    try:
        response = requests.get(endpoint, params=params, headers=COMMON_HEADERS, timeout=10)
        return _handle_response(response, "fetch_vehicle_specs")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for fetch_vehicle_specs."}


def fetch_vehicle_makes(year: str) -> dict:
    """Calls the Node.js API to get vehicle makes for a given year."""
    endpoint = f"{API_BASE_URL}/function/makes"
    params = {"year": year}
    logger.info(f"Calling API: GET {endpoint} with year: {year}")
    try:
        response = requests.get(endpoint, params=params, headers=COMMON_HEADERS, timeout=10)
        return _handle_response(response, "fetch_vehicle_makes")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for fetch_vehicle_makes."}


def fetch_vehicle_models(make: str, year: str) -> dict:
    """Calls the Node.js API to get vehicle models for a given make and year."""
    endpoint = f"{API_BASE_URL}/function/model"
    params = {"make": make, "year": year}
    logger.info(f"Calling API: GET {endpoint} with make: {make}, year: {year}")
    try:
        response = requests.get(endpoint, params=params, headers=COMMON_HEADERS, timeout=10)
        return _handle_response(response, "fetch_vehicle_models")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for fetch_vehicle_models."}


def fetch_vehicle_years(make: str, model: str) -> dict:
    """Calls the Node.js API to get vehicle years for a given make and model."""
    endpoint = f"{API_BASE_URL}/function/year"
    params = {"make": make, "model": model}
    logger.info(f"Calling API: GET {endpoint} with make: {make}, model: {model}")
    try:
        response = requests.get(endpoint, params=params, headers=COMMON_HEADERS, timeout=10)
        return _handle_response(response, "fetch_vehicle_years")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for fetch_vehicle_years."}


def submit_for_quote(payload: dict) -> dict:
    """Calls the Node.js API to submit details for a trucking price quote."""
    endpoint = f"{API_BASE_URL}/trucking/check/prices"
    logger.info(f"Calling API: POST {endpoint} with payload: {json.dumps(payload)[:200]}...") # Log truncated payload
    try:
        response = requests.post(endpoint, json=payload, headers=COMMON_HEADERS, timeout=20) # Longer timeout for potential processing
        # The actual quote ID is in a top-level "quote" field, not necessarily in the "data" field for this specific API.
        # The _handle_response will give us the parsed JSON. We let the tool layer extract the quote ID.
        return _handle_response(response, "submit_for_quote")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for submit_for_quote."}
    except Exception as e:
        logger.error(f"Unexpected error in submit_for_quote during request: {e}")
        return {"error": True, "message": f"An unexpected error occurred: {str(e)}"}


def fetch_quote_details(quote_id: str) -> dict:
    """Calls the Node.js API to get details for a specific quote ID."""
    endpoint = f"{API_BASE_URL}/search/quote/{quote_id}" # Path parameter, not query
    logger.info(f"Calling API: GET {endpoint}")
    try:
        response = requests.get(endpoint, headers=COMMON_HEADERS, timeout=10)
        return _handle_response(response, "fetch_quote_details")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for fetch_quote_details."}

def search_trucking_orders(search_query: str = None, limit: int = 10, page: int = 1) -> dict:
    """Calls the Node.js API to search a user's trucking orders."""
    if not AUTH_TOKEN:
        return {"error": True, "message": "You must be logged in to perform this action."}
    endpoint = f"{API_BASE_URL}/trucking"
    params = {"limit": limit, "page": page}
    if search_query:
        params["search"] = search_query
    logger.info(f"Calling API: GET {endpoint} with params: {params}")
    try:
        response = requests.get(endpoint, params=params, headers=_get_auth_headers(), timeout=15)
        return _handle_response(response, "search_trucking_orders")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for search_trucking_orders."}

def search_bookings(search_query: str = None, type_vehicle: str = None, type_shipping: str = None, done: bool = None, limit: int = 10, page: int = 1) -> dict:
    """Calls the Node.js API for advanced search of a user's bookings."""
    if not AUTH_TOKEN:
        return {"error": True, "message": "You must be logged in to perform this action."}
    endpoint = f"{API_BASE_URL}/booking"
    params = {"limit": limit, "page": page}
    if search_query:
        params["search"] = search_query
    if type_vehicle:
        params["typeVehicle"] = type_vehicle
    if type_shipping:
        params["typeShipping"] = type_shipping
    if done is not None:
        params["done"] = str(done).lower()
    logger.info(f"Calling API: GET {endpoint} with params: {params}")
    try:
        response = requests.get(endpoint, params=params, headers=_get_auth_headers(), timeout=15)
        return _handle_response(response, "search_bookings")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for search_bookings."}

def create_trucking_order(payload: dict) -> dict:
    """Calls the Node.js API to convert a quote into a booked order."""
    if not AUTH_TOKEN:
        return {"error": True, "message": "You must be logged in to book a shipment."}
    endpoint = f"{API_BASE_URL}/trucking"
    logger.info(f"Calling API: POST {endpoint} to create an order.")
    try:
        response = requests.post(endpoint, json=payload, headers=_get_auth_headers(), timeout=20)
        return _handle_response(response, "create_trucking_order")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {endpoint}")
        return {"error": True, "message": "API request timed out for create_trucking_order."}

# Example of how to test one of these functions directly (for development)
if __name__ == '''__main__''':
    logging.basicConfig(level=logging.INFO)
    # Ensure API_BASE_URL is set in your environment or .env file for this to work
    # For example, export API_BASE_URL='http://your-api-domain.com/api/v1'
    
    print("Testing fetch_vehicle_specs...")
    # Replace with a known working VIN if you have one for your test API
    # spec_data = fetch_vehicle_specs("1HGCM82633A123456") 
    # print(json.dumps(spec_data, indent=2))

    # print("\nTesting fetch_vehicle_makes...")
    # makes_data = fetch_vehicle_makes("2020")
    # print(json.dumps(makes_data, indent=2))

    # print("\nTesting fetch_vehicle_models...")
    # models_data = fetch_vehicle_models("Toyota", "2024") # Make sure Toyota is a valid make for 2024 in your API
    # print(json.dumps(models_data, indent=2))

    # print("\nTesting fetch_vehicle_years...")
    # years_data = fetch_vehicle_years("Toyota", "RAV4") # Make sure RAV4 is a valid model for Toyota
    # print(json.dumps(years_data, indent=2))

    # print("\nTesting submit_for_quote...")
    # quote_payload = {
    #     "Ip": "192.168.1.100", # Dynamic IP would be better
    #     "firstname": "Test", "lastname": "User", "email": "test@example.com",
    #     "country": "United States", "state": "New York", "city": "Albany County",
    #     "offerPrice": "0", # As per spec
    #     "stopNumber1": {"city": "Albany County", "state": "New York", "country": "United States", "code": "12110"},
    #     "stopNumber2": {"city": "Harris County", "state": "Texas", "country": "United States", "code": "77024"},
    #     "vehicles": [{"year": "2020", "make": "Toyota", "model": "RAV4", "vehicleType": "SUV", "operable": True, "pickUpStopNumber": 1, "dropOffStopNumber": 2}]
    # }
    # quote_response = submit_for_quote(quote_payload)
    # print(json.dumps(quote_response, indent=2))
    # if not quote_response.get("error") and quote_response.get("quote"):
    #     quote_id_to_test = quote_response.get("quote")
    #     print(f"\nSuccessfully submitted quote. Quote ID: {quote_id_to_test}")
    #     print("\nTesting fetch_quote_details...")
    #     details_response = fetch_quote_details(quote_id_to_test)
    #     print(json.dumps(details_response, indent=2))
    # else:
    #     print("\nSkipping fetch_quote_details due to issues in submit_for_quote or missing quote ID.")
    pass # Remove pass and uncomment tests above for direct execution 