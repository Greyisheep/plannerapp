from ..services import node_api_service
import logging

logger = logging.getLogger(__name__)

def login_user(email: str, password: str) -> dict:
    """Logs in a user with their email and password to enable access to protected services."""
    logger.info(f"Tool: login_user called for email: {email}")
    if not email or not password:
        return {"error": True, "message": "Email and password are required."}
    
    # We now directly call the login service, which handles the token.
    # The service layer is responsible for storing the token globally.
    result = node_api_service.login(email, password)

    if result.get("success"):
        # The ADK doesn't need the full user object, just a success message.
        # The service layer now holds the token for subsequent calls.
        return {"success": True, "message": "Login successful."}
    else:
        # Pass along the error from the service layer.
        return result

def get_current_user_profile() -> dict:
    """Fetches the profile of the currently logged-in user."""
    logger.info("Tool: get_current_user_profile called.")
    return node_api_service.get_user_profile() 