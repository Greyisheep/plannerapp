import logging
import os

from dotenv import load_dotenv

# ADK Components
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Import the tools we created
from .adk_math_tool import solve_math_expression
from .adk_file_io_tool import FileIOTool
from .adk_sms_tool import SmsTool
from .adk_calls_tool import CallsTool

# Load environment variables from .env file (especially for TWILIO and GOOGLE_CLOUD_PROJECT/LOCATION)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Initialize Tools (Globally) ---
# Math tool is a direct function
math_tool = solve_math_expression # Direct function reference

# FileIO tool needs instantiation to set the base directory
# We want to use the same 'app_io_files' directory as the original Azure app for consistency
file_io_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app_io_files") # Path relative to this file's location
if not os.path.exists(file_io_base_dir):
    os.makedirs(file_io_base_dir)
    logger.info(f"Created base directory for FileIOTool: {file_io_base_dir}")
file_tool_instance = FileIOTool(base_directory=file_io_base_dir)

# Twilio tools also need instantiation
sms_tool_instance = SmsTool()
calls_tool_instance = CallsTool()

# Explicitly create FunctionTool instances for each method
file_io_tools = [
    FunctionTool(func=file_tool_instance.write_to_file),
    FunctionTool(func=file_tool_instance.append_to_file),
    FunctionTool(func=file_tool_instance.read_file_content),
    FunctionTool(func=file_tool_instance.delete_file_by_name),
]

sms_tools = [
    FunctionTool(func=sms_tool_instance.send_sms),
    FunctionTool(func=sms_tool_instance.send_mms),
]

calls_tools = [
    FunctionTool(func=calls_tool_instance.make_call),
]

all_tools = [
    FunctionTool(func=math_tool) # Ensure math_tool is also wrapped if it's a function reference
    ] + file_io_tools + sms_tools + calls_tools

# --- Configure and Define the Global LLM Agent ---
# Check for Google AI Studio configuration first
google_api_key = os.getenv("GOOGLE_API_KEY")
use_vertex_ai_env = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() # Default to FALSE

llm_model_name = "gemini-2.5-flash-preview-05-20" # A good default

if use_vertex_ai_env == "FALSE" and google_api_key:
    logger.info(f"Configuring LlmAgent for Google AI Studio with API Key using model: {llm_model_name}.")
elif use_vertex_ai_env == "TRUE":
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    if not project_id or not location:
        logger.error(
            "GOOGLE_GENAI_USE_VERTEXAI is TRUE, but GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_LOCATION "
            "environment variables are not set. LLM agent will likely fail to initialize."
        )
        # Potentially raise an error or set agent to None to prevent partial initialization
    else:
        logger.info(f"Configuring LlmAgent for Vertex AI in {project_id}/{location} using model: {llm_model_name}.")
else:
    logger.error(
        "LLM configuration is unclear or incomplete. "
        "For Google AI Studio: set GOOGLE_GENAI_USE_VERTEXAI=FALSE and provide GOOGLE_API_KEY. "
        "For Vertex AI: set GOOGLE_GENAI_USE_VERTEXAI=TRUE (or leave unset) and provide GOOGLE_CLOUD_PROJECT & GOOGLE_CLOUD_LOCATION."
    )
    # Potentially raise an error or set agent to None

planner_instruction = (
    "You are a helpful AI assistant. You have a variety of tools available. "
    "When a user asks for something, first consider if any of your tools can help. "
    "If so, call the appropriate tool(s) by outputting a function call. "
    "If not, respond directly to the user. "
    "When using tools, the results will be provided to you. Use these results to formulate your final response to the user. "
    "Available tools can solve math, perform file operations (read, write, append, delete in a specific directory), send SMS/MMS, and make calls."
)

# Define the root_agent globally
try:
    root_agent = LlmAgent(
        model=llm_model_name,
        name="GlobalPlannerAgent", # Ensure this name is unique if running multiple agents
        description="A helpful assistant that can use tools for math, files, SMS, and calls.",
        instruction=planner_instruction,
        tools=all_tools
    )
    logger.info(f"GlobalPlannerAgent initialized with model '{llm_model_name}'.")
except Exception as e:
    logger.error(f"Failed to initialize LlmAgent globally: {e}")
    logger.error(
        "Please ensure your environment variables for Google AI Studio (GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI=FALSE) "
        "or Vertex AI (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI=TRUE) are correctly set. "
        "If using Vertex AI, ensure you have authenticated with `gcloud auth application-default login`."
    )
    root_agent = None # Set to None if initialization fails


if __name__ == "__main__":
    # This block is typically not used when running with `adk run` or `adk web`,
    # as those tools import the `root_agent` directly.
    # However, you can add test code or a simple CLI interaction here if needed for direct script execution.
    
    logger.info("ADK Planner Agent Script - Loaded")
    if root_agent is None:
        logger.error("root_agent could not be initialized. Exiting.")
    else:
        logger.info(f"root_agent '{root_agent.name}' is defined and ready.")
        logger.info("To interact with this agent, use 'adk run ADK' or 'adk web' from the parent directory.")
        logger.info("Or, you can add custom test/interaction code within this '__main__' block for direct execution.")

    # Clearer alias/warning section - can remain if useful
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        logger.warning(
            "Found AZURE_OPENAI_ENDPOINT. This ADK PlannerApp uses Google Gemini. "
            "Please ensure GOOGLE_API_KEY (for AI Studio) or GOOGLE_CLOUD_PROJECT/LOCATION (for Vertex AI) are set."
        )

    if not os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_SID"): # SK used TWILIO_SID
         os.environ["TWILIO_ACCOUNT_SID"] = os.getenv("TWILIO_SID")
         logger.info("Used TWILIO_SID as TWILIO_ACCOUNT_SID for ADK Twilio tools.")
