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

all_tools = [
    get_vehicle_specs_tool,
    get_vehicle_makes_tool,
    get_vehicle_models_tool,
    get_vehicle_years_tool,
    get_price_quote_tool,
    get_quote_details_tool
]
logger.info(f"{len(all_tools)} tools initialized.")

# --- Define Agent Instruction --- 
agent_instruction = (
    "You are DockMind, a specialized AI assistant for vehicle information and shipping logistics. "
    "Your primary functions are to help users look up vehicle specifications using a VIN, "
    "find vehicle makes, models, and years, and provide trucking price quotes. "
    "You can also retrieve details of a previously generated quote using a quote ID.\n\n"
    "When a user asks for information, first determine if one of your specialized tools can fulfill the request. "
    "Your available tools are:\n"
    "- get_vehicle_specs_by_vin: Use this to get detailed specs for a car if the user provides a VIN.\n"
    "- get_vehicle_makes_for_year: Use this if a user wants to know car makes available for a specific year.\n"
    "- get_vehicle_models_for_make_year: Use this if a user provides a car make and year and wants to see models.\n"
    "- get_vehicle_years_for_make_model: Use this if a user provides a car make and model and wants to know available years.\n"
    "- get_trucking_price_quote: Use this to calculate a shipping quote. You will need origin (city, state, zip, country), "
    "  destination (city, state, zip, country), and vehicle details (year, make, model, type, operable status). Collect all necessary details before calling.\n"
    "- get_quote_details_by_id: Use this if a user provides a quote ID and wants to see its details.\n\n"
    "If a tool is appropriate, clearly state you are using a tool and then output the function call. "
    "If the user's query is outside these functions (e.g., general chit-chat, or a request you cannot fulfill with these tools), "
    "respond politely and indicate the limits of your current capabilities. "
    "Always present tool results clearly to the user. If a tool call results in an error, inform the user clearly about the error."
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