from ..services import node_api_service
import logging

logger = logging.getLogger(__name__)

def get_vehicle_specs_by_vin(vin: str) -> dict:
    """Fetches detailed vehicle specifications based on its Vehicle Identification Number (VIN)."""
    logger.info(f"Tool: get_vehicle_specs_by_vin called for VIN: {vin}")
    if not vin or not isinstance(vin, str):
        logger.error("Invalid VIN provided to get_vehicle_specs_by_vin.")
        return {"error": True, "message": "Invalid VIN provided."}
    result = node_api_service.fetch_vehicle_specs(vin)
    if result.get("error"):
        logger.error(f"API error fetching vehicle specs for VIN {vin}: {result.get('message')}")
    return result

def get_vehicle_makes_for_year(year: str) -> dict:
    """Lists available vehicle makes for a given year. The year should be a 4-digit number."""
    logger.info(f"Tool: get_vehicle_makes_for_year called for year: {year}")
    if not year or not (isinstance(year, str) and year.isdigit() and len(year) == 4):
        logger.error("Invalid year provided to get_vehicle_makes_for_year. Must be a 4-digit string.")
        return {"error": True, "message": "Invalid year provided. Must be a 4-digit string."}
    result = node_api_service.fetch_vehicle_makes(year)
    if result.get("error"):
        logger.error(f"API error fetching vehicle makes for year {year}: {result.get('message')}")
    return result

def get_vehicle_models_for_make_year(make: str, year: str) -> dict:
    """Lists available vehicle models for a given make and year. The year should be a 4-digit number."""
    logger.info(f"Tool: get_vehicle_models_for_make_year called for make: {make}, year: {year}")
    if not make or not isinstance(make, str):
        logger.error("Invalid make provided to get_vehicle_models_for_make_year.")
        return {"error": True, "message": "Invalid make provided."}
    if not year or not (isinstance(year, str) and year.isdigit() and len(year) == 4):
        logger.error("Invalid year provided to get_vehicle_models_for_make_year. Must be a 4-digit string.")
        return {"error": True, "message": "Invalid year provided. Must be a 4-digit string."}
    result = node_api_service.fetch_vehicle_models(make, year)
    if result.get("error"):
        logger.error(f"API error fetching models for make {make}, year {year}: {result.get('message')}")
    return result

def get_vehicle_years_for_make_model(make: str, model: str) -> dict:
    """Lists available model years for a given make and model."""
    logger.info(f"Tool: get_vehicle_years_for_make_model called for make: {make}, model: {model}")
    if not make or not isinstance(make, str):
        logger.error("Invalid make provided to get_vehicle_years_for_make_model.")
        return {"error": True, "message": "Invalid make provided."}
    if not model or not isinstance(model, str):
        logger.error("Invalid model provided to get_vehicle_years_for_make_model.")
        return {"error": True, "message": "Invalid model provided."}
    result = node_api_service.fetch_vehicle_years(make, model)
    if result.get("error"):
        logger.error(f"API error fetching years for make {make}, model {model}: {result.get('message')}")
    return result 