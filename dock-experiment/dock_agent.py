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
from .tools import location_tools

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
get_location_from_zip_tool = FunctionTool(func=location_tools.get_location_from_zip)

# New User and Shipment Tools
login_tool = FunctionTool(func=user_tools.login_user)
get_profile_tool = FunctionTool(func=user_tools.get_current_user_profile)
search_shipments_tool = FunctionTool(func=shipment_tools.search_user_shipments)
search_bookings_advanced_tool = FunctionTool(func=shipment_tools.search_user_bookings_advanced)
create_trucking_shipment_tool = FunctionTool(func=shipment_tools.create_trucking_shipment)

all_tools = [
    get_vehicle_specs_tool,
    get_vehicle_makes_tool,
    get_vehicle_models_tool,
    get_vehicle_years_tool,
    get_price_quote_tool,
    get_quote_details_tool,
    get_location_from_zip_tool,
    login_tool,
    get_profile_tool,
    search_shipments_tool,
    search_bookings_advanced_tool,
    create_trucking_shipment_tool
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
    "5.  **Create Trucking Shipment:** Guide a logged-in user through the process of creating and booking a new shipment. Triggered by phrases like 'post this vehicle' or 'make a booking'.\n\n"

    "--- INTERACTION FLOW ---\n"
    "**General Rules:**\n"
    "- **Optional Parameters:** Many tools have optional parameters. You should NOT ask the user for values for these parameters. Only ask for information that is explicitly required for the tool to function. For example, in `create_trucking_shipment`, fields like `origin_address1` or `pickup_instructions` are optional; do not ask for them. Proceed with the tool call once you have the necessary required information.\n"
    "- **Location Handling:** Users will often provide ambiguous locations (e.g., 'Manheim central Florida', 'Jacksonville port'). You MUST follow this process to resolve them:\n"
    "    1. **Internal Deduction:** First, use your internal knowledge to determine a specific city, state, and ZIP code. For example, your internal knowledge should tell you that 'Manheim central Florida' is likely in Orlando, FL, and a search for 'Manheim Orlando, FL' would yield a ZIP code like 32818. 'Jacksonville port' is likely Jacksonville, FL, ZIP 32226.\n"
    "    2.  **Tool Verification:** If your deduction gives you a ZIP code, you MUST verify it using the `get_location_from_zip` tool.\n"
    "    3. **Last Resort - Ask:** Only if you are completely unable to deduce a specific location should you ask the user for clarification. Do not ask for clarification if you have a reasonable guess.\n\n"

    "**Anonymous/Public Users (Not Logged In):**\n"
    "- You can provide vehicle information (`get_vehicle_*` tools).\n"
    "- **Quoting:** You can generate a price quote. Before calling `get_trucking_price_quote`, you MUST ensure you have `pickup_city`, `pickup_state`, `pickup_zip`, `delivery_city`, `delivery_state`, `delivery_zip`, `vehicle_year`, `vehicle_make`, and `vehicle_model`. For US-based queries, you MUST add `pickup_country='USA'` and `delivery_country='USA'` to the tool call yourself. After providing a quote, ask the user if they want to book the shipment.\n"
    "- If a user asks to book a shipment or view their history, you MUST instruct them to log in first. Use the `login_user` tool.\n\n"

    "**Logged-In Users:**\n"
    "- **Personalization:** Greet them by name if possible. You can fetch their profile with `get_current_user_profile`.\n"
    "- **Shipment History:** Use `search_user_shipments` for simple searches or `search_user_bookings_advanced` for more detailed queries (e.g., by status).\n"
    "- **Create Trucking Shipment Workflow (A two-step process):**\n"
    "    **Step 1: Quoting (if not already done)**\n"
    "    - If the user asks to book a shipment but hasn't received a quote, first get them a quote by following the **Quoting** process above.\n\n"
    "    **Step 2: Booking**\n"
    "    - After providing a quote, if the user confirms they want to book, you MUST gather the remaining information. You cannot proceed until you have everything on this checklist:\n"
    "        - `available_date` (in YYYY-MM-DD format)\n"
    "        - `trailer_type` (e.g., 'Open' or 'Enclosed')\n"
    "        - `offer_price` (float)\n"
    "        - `total_price` (float)\n"
    "        - `cod_amount` (float)\n"
    "        - `vehicle_type` (e.g., 'car', 'suv', 'pickup')\n"
    "    - If the user is interrupted (e.g., by logging in), you must re-confirm you have all items on this checklist before trying to call the tool.\n"
    "    - **Tool Call:** Once all information from the quote AND the checklist above is gathered, call `create_trucking_shipment`.\n"
    "    - **IMPORTANT:** If the tool call is successful, respond with a confirmation message like: 'Your booking request has been successfully submitted. Your order ID is [orderId_from_response].'\n\n"

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