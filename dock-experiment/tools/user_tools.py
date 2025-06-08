from ..services import node_api_service
import logging

logger = logging.getLogger(__name__)

def login_user(email: str, password: str) -> dict:
    """Logs in a user with their email and password to enable access to protected services."""
    logger.info(f"Tool: login_user called for email: {email}")
    if not email or not password:
        return {"error": True, "message": "Email and password are required."}
    return node_api_service.login(email, password)

def get_current_user_profile() -> dict:
    """Fetches the profile of the currently logged-in user."""
    logger.info("Tool: get_current_user_profile called.")
    return node_api_service.get_user_profile() 