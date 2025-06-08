import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import your tools
from .tools import vehicle_tools
from .tools import quoting_tools
from .tools import user_tools
from .tools import shipment_tools

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger.info("DockMind Agent loading...")

# --- Initialize Tools (Globally) ---
# The ADK will use the function's docstring as its description to the LLM
logger.info("Initializing tools...")
get_vehicle_specs_tool = FunctionTool(func=vehicle_tools.get_vehicle_specs_by_vin)
get_vehicle_makes_tool = FunctionTool(func=vehicle_tools.get_vehicle_makes_for_year)
get_vehicle_models_tool = FunctionTool(func=vehicle_tools.get_vehicle_models_for_make_year)
get_vehicle_years_tool = FunctionTool(func=vehicle_tools.get_vehicle_years_for_make_model)

get_price_quote_tool = FunctionTool(func=quoting_tools.get_trucking_price_quote)
get_quote_details_tool = FunctionTool(func=quoting_tools.get_quote_details_by_id)

# New User and Shipment Tools
login_tool = FunctionTool(func=user_tools.login_user)
get_profile_tool = FunctionTool(func=user_tools.get_current_user_profile)
search_shipments_tool = FunctionTool(func=shipment_tools.search_user_shipments)
search_bookings_advanced_tool = FunctionTool(func=shipment_tools.search_user_bookings_advanced)
book_shipment_tool = FunctionTool(func=shipment_tools.book_shipment_order)

all_tools = [
    get_vehicle_specs_tool,
    get_vehicle_makes_tool,
    get_vehicle_models_tool,
    get_vehicle_years_tool,
    get_price_quote_tool,
    get_quote_details_tool,
    login_tool,
    get_profile_tool,
    search_shipments_tool,
    search_bookings_advanced_tool,
    book_shipment_tool
]
logger.info(f"{len(all_tools)} tools initialized.")

# --- Define Agent Instruction --- 
agent_instruction = (
    "You are DockMind, a specialized AI assistant for vehicle information and shipping logistics. "
    "You have two main roles: an anonymous Quoting Assistant and a personalized Booking and Tracking Assistant.\n\n"
    
    "--- CORE CAPABILITIES ---\n"
    "1.  **Vehicle Information:** Look up vehicle specs by VIN, and find makes, models, and years.\n"
    "2.  **Price Quotes:** Provide trucking price quotes based on origin, destination, and vehicle details.\n"
    "3.  **User Accounts:** Allow users to log in to access personalized services.\n"
    "4.  **Shipment Tracking:** Search a logged-in user's shipment history and check their status.\n"
    "5.  **Booking:** Guide a logged-in user through the process of booking a shipment after they receive a quote.\n\n"

    "--- INTERACTION FLOW ---\n"
    "**Anonymous/Public Users (Not Logged In):**\n"
    "- You can provide vehicle information (`get_vehicle_*` tools).\n"
    "- You can generate a price quote (`get_trucking_price_quote`).\n"
    "- If a user asks to book a shipment or view their history, you MUST instruct them to log in first. Use the `login_user` tool.\n\n"

    "**Logged-In Users:**\n"
    "- **Personalization:** Greet them by name if possible. You can fetch their profile with `get_current_user_profile`.\n"
    "- **Shipment History:** Use `search_user_shipments` for simple searches or `search_user_bookings_advanced` for more detailed queries (e.g., by status).\n"
    "- **Booking Workflow:**\n"
    "    1. After providing a quote with `get_trucking_price_quote`, ask the user if they want to book it.\n"
    "    2. If they say yes, confirm they are logged in. (If you aren't sure, you can use `get_current_user_profile` and check for an error).\n"
    "    3. To book, you MUST use the `book_shipment_order` tool. You will need to gather all the parameters required by the tool. Many of these will be available from the quoting process.\n"
    "    4. **IMPORTANT:** The final booking step might fail due to an external partner system. If you use `book_shipment_order` and do NOT get an error, respond with a confirmation message like: 'Your booking request has been successfully submitted to our system. You will receive an email confirmation from our team as soon as it is processed by our logistics partner. Your order ID is [orderId_from_response].'\n\n"
    
    "Always be polite and clear. If you need information, ask for it. If a tool fails, clearly state the error to the user."
)

# --- Define the LLM Agent (Globally) ---
logger.info("Initializing LlmAgent...")
# Configure the model name via an environment variable or a .env file
# Default to gemini-2.5-flash-preview-05-20 if ADK_MODEL_NAME is not set
llm_model_name = os.getenv("ADK_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
if llm_model_name == "gemini-2.5-flash-preview-05-20" and not os.getenv("ADK_MODEL_NAME"):
    logger.info("Using default LLM model: gemini-2.5-flash-preview-05-20 (ADK_MODEL_NAME not set).")
else:
    logger.info(f"Using LLM model: {llm_model_name} (from ADK_MODEL_NAME environment variable).")

try:
    agent = LlmAgent(
        model=llm_model_name,
        name="DockMindAgent",
        description="An agent to assist with vehicle information and shipping quotes.",
        instruction=agent_instruction,
        tools=all_tools,
        # verbose=True # Optional: for more detailed ADK logging, enable if needed
    )
    logger.info(f"DockMind Agent '{agent.name}' initialized successfully with model '{llm_model_name}'.")
    logger.info("Available tools:")
    for i, tool in enumerate(agent.tools):
        logger.info(f"  Tool {i+1}: {tool.name} - {tool.description}")
    logger.info("Agent ready for ADK web/run.")
except Exception as e:
    logger.error(f"Failed to initialize LlmAgent: {e}", exc_info=True)
    logger.error(
        "Please ensure your GOOGLE_API_KEY is correctly set in your environment or .env file. "
        "If you intended to use a specific model via ADK_MODEL_NAME, ensure it's a valid model identifier."
    )
    agent = None # Set agent to None if initialization fails

if __name__ == "__main__":
    # This block is typically not used when running with `adk run` or `adk web`,
    # as those tools import the `agent` directly.
    logger.info("DockMind Agent script loaded for direct execution (e.g., python dock_agent.py).")
    if agent is None:
        logger.error("DockMind Agent (agent) could not be initialized. Cannot run directly. Please check logs for errors.")
    else:
        logger.info(f"Global agent '{agent.name}' is defined and ready.")
        logger.info("To interact with this agent via a web interface, use 'adk web dock_agent' from the 'dock-experiment' directory.")
        logger.info("Ensure GOOGLE_API_KEY, API_BASE_URL, and optionally ADK_MODEL_NAME environment variables are set (e.g., in a .env file).")
        logger.info("Example queries you could try with adk web/run:")
        logger.info("- What are the specs for VIN 1HGCM82633A123456?")
        logger.info("- What vehicle makes are available for the year 2022?")
        logger.info("- Get me a trucking quote from Los Angeles, CA, 90001, USA to Newark, NJ, 07101, USA for a 2021 Honda CRV.")
        logger.info("- What are the details for quote ID fe7b062b-e33a-4205-9dd3-1ac9404bb4f6?")
        logger.info("- Please log me in. My email is user@example.com and my password is 'password'.")
        logger.info("- Who am I logged in as?")
        logger.info("- Show me my past shipments.") 