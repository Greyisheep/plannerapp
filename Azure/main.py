import asyncio
import logging
import os
import json

from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
# Import plugins
from math_plugin import MathPlugin
from file_io_plugin import FileIOPlugin
from sms_plugin import SmsPlugin
from calls_plugin import CallsPlugin

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("======== Python Semantic Kernel Planner App ========")

    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_model_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") # SK Python uses DEPLOYMENT_NAME
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not all([azure_openai_endpoint, azure_openai_model_id, azure_openai_api_key]):
        logger.error("Azure OpenAI credentials (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_KEY) not set in environment variables.")
        return

    kernel = Kernel()

    chat_service = AzureChatCompletion(
        deployment_name=azure_openai_model_id,
        endpoint=azure_openai_endpoint,
        api_key=azure_openai_api_key,
    )
    kernel.add_service(chat_service)
    logger.info(f"Kernel initialized with Azure OpenAI Chat Completion service (Deployment: {azure_openai_model_id}).")

    # Add plugins
    # The second argument is the plugin_name the LLM will use to call the plugin.
    kernel.add_plugin(MathPlugin(), plugin_name="MathSolver") # Matching C# MathSolver
    logger.info("MathPlugin loaded as MathSolver.")

    # For FileIOPlugin, you can specify a base directory if needed, e.g., FileIOPlugin(\\"./data\\")
    # If None, it defaults to the current working directory, with safety checks.
    kernel.add_plugin(FileIOPlugin(base_directory="app_io_files"), plugin_name="FileIO") 
    logger.info("FileIOPlugin loaded as FileIO. Files will be relative to 'app_io_files' directory.")
    # Ensure the directory for FileIOPlugin exists
    if not os.path.exists("app_io_files"):
        os.makedirs("app_io_files")
        logger.info("Created 'app_io_files' directory for FileIOPlugin.")


    # Twilio plugins require credentials. They will log errors if not configured.
    # Check if Twilio env vars are present before loading to give a clearer startup message.
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_FROM_PHONE")

    if all([twilio_sid, twilio_auth, twilio_phone]):
        kernel.add_plugin(SmsPlugin(), plugin_name="SmsSender") 
        logger.info("SmsPlugin loaded as SmsSender.")
        kernel.add_plugin(CallsPlugin(), plugin_name="CallMaker")
        logger.info("CallsPlugin loaded as CallMaker.")
    else:
        logger.warning("Twilio credentials not fully set. SmsSender and CallMaker plugins will not be fully functional.")
        # Add them anyway so the app doesn't crash if they are called, they have internal checks.
        kernel.add_plugin(SmsPlugin(), plugin_name="SmsSender") 
        kernel.add_plugin(CallsPlugin(), plugin_name="CallMaker")


    chat_history = ChatHistory()
    # System message to guide the AI. Similar to what might be implicitly happening or explicitly set in SK C#.
    chat_history.add_system_message(
        "You are a helpful AI assistant. You have a variety of tools available. "
        "When a user asks for something, first consider if any of your tools can help. "
        "If so, call the appropriate tool(s). If not, respond directly to the user. "
        "When using tools, the results will be provided to you. Use these results to formulate your final response to the user."
        "Available tools: MathSolver, FileIO, SmsSender, CallMaker."
    )


    print("User > ", end="")
    try:
        while (user_input := await asyncio.to_thread(input)) :
            if user_input.lower() == "exit":
                print("Exiting application.")
                break
            
            chat_history.add_user_message(user_input)
            logger.info(f"User input: {user_input}")

            # Get execution settings for the chat service
            execution_settings = kernel.get_prompt_execution_settings_from_service_id(
                service_id=chat_service.service_id,
            )
            
            # Configure tools for the chat service
            tools = []
            for plugin_name, plugin in kernel.plugins.items():
                for function_name, function_metadata in plugin.functions.items():
                    # Format parameters according to OpenAI an JSON Schema spec
                    # https://json-schema.org/understanding-json-schema/reference/object.html#properties
                    # https://platform.openai.com/docs/guides/function-calling
                    function_params = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                    # Basic type mapping from Python to JSON Schema
                    def get_json_type(python_type_str):
                        if python_type_str == "str":
                            return "string"
                        if python_type_str == "int":
                            return "integer"
                        if python_type_str == "float" or python_type_str == "Decimal":
                            return "number"
                        if python_type_str == "bool":
                            return "boolean"
                        if python_type_str == "list" or python_type_str == "array":
                            return "array"
                        if python_type_str == "dict" or python_type_str == "object":
                            return "object"
                        return "string"  # Default to string if unknown

                    for param in function_metadata.parameters:
                        param_type = param.type_ if param.type_ else "string"
                        function_params["properties"][param.name] = {
                            "type": get_json_type(param_type),
                            "description": param.description
                        }
                        if param.is_required:
                            function_params["required"].append(param.name)
                    
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": f"{plugin_name}_{function_metadata.name}", # Use underscore for OpenAI compatibility
                            "description": function_metadata.description,
                            "parameters": function_params
                        }
                    })
            
            # Set tools in execution settings
            execution_settings.tools = tools
            execution_settings.tool_choice = "auto"

            print("Assistant > ", end="")
            response = await chat_service.get_chat_message_contents(
                chat_history=chat_history,
                settings=execution_settings
            )
            
            if response:
                # Assuming the first response in the list is the one we want
                if isinstance(response, list) and len(response) > 0:
                    # If the response contains tool calls, they will be in response[0].tool_calls
                    # If it's a direct message, it will be in response[0].content
                    # For now, we will just extract the primary content if available.
                    # Proper tool call handling would require invoking the tools and sending results back.
                    
                    # Check for tool calls first by inspecting items in the ChatMessageContent
                    tool_calls_present = False
                    if hasattr(response[0], 'items') and response[0].items:
                        for item in response[0].items:
                            if isinstance(item, FunctionCallContent):
                                tool_calls_present = True
                                break
                    
                    if tool_calls_present:
                        # Add the assistant's message containing the tool call requests to history
                        chat_history.add_message(response[0])

                        # Process each tool call
                        for tool_call in response[0].items:
                            if not isinstance(tool_call, FunctionCallContent):
                                continue

                            logger.info(f"Executing tool call: {tool_call.name} with ID: {tool_call.id}")
                            try:
                                # Parse arguments if they are a string
                                try:
                                    tool_args = json.loads(tool_call.arguments)
                                except json.JSONDecodeError:
                                    # Fallback if arguments are not a valid JSON string (should ideally be)
                                    # Or if the arguments are already a dict (though API usually sends string)
                                    if isinstance(tool_call.arguments, dict):
                                        tool_args = tool_call.arguments
                                    else: # If it's a plain string not meant to be JSON, pass as is if your function expects that
                                          # This part needs careful handling based on how functions are defined.
                                          # For now, let's assume functions might expect a single string arg if not JSON.
                                        tool_args = {"input": tool_call.arguments} # Or handle based on specific function needs
                                        logger.warning(f"Tool call arguments for {tool_call.name} were not valid JSON. Attempting fallback.")

                                plugin_name, function_name = tool_call.name.split("_", 1)
                                
                                # Invoke the function
                                # Ensure KernelArguments are correctly formed for the function call
                                kernel_args = KernelArguments(**tool_args)
                                result = await kernel.invoke(plugin_name=plugin_name, function_name=function_name, arguments=kernel_args)
                                
                                # Get the primary result value
                                result_value = str(result.value) if result and hasattr(result, 'value') else str(result)

                                logger.info(f"Tool call {tool_call.name} result: {result_value}")
                                
                                # Add tool result to chat history
                                tool_response_message_content = FunctionResultContent(id=tool_call.id, name=tool_call.name, result=result_value)
                                tool_chat_message = ChatMessageContent(
                                    role="tool",
                                    items=[tool_response_message_content],
                                    metadata={"tool_call_id": tool_call.id} # Ensure metadata is at ChatMessageContent level too if needed
                                )
                                chat_history.add_message(tool_chat_message)

                            except Exception as e:
                                logger.error(f"Error executing tool {tool_call.name}: {e}")
                                error_result = f"Error: {e}"
                                tool_response_message_content = FunctionResultContent(id=tool_call.id, name=tool_call.name, result=error_result)
                                tool_chat_message = ChatMessageContent(
                                    role="tool",
                                    items=[tool_response_message_content],
                                    metadata={"tool_call_id": tool_call.id}
                                )
                                chat_history.add_message(tool_chat_message)
                        
                        # Now that tool results are in history, call the model again to get the final response
                        logger.info("Calling LLM again with tool results.")
                        final_response_messages = await chat_service.get_chat_message_contents(
                            chat_history=chat_history,
                            settings=execution_settings
                        )

                        if final_response_messages and isinstance(final_response_messages, list) and len(final_response_messages) > 0:
                            if final_response_messages[0].content:
                                full_message = str(final_response_messages[0].content)
                                print(full_message)
                                chat_history.add_assistant_message(full_message)
                            else:
                                full_message = "[Assistant did not provide content after tool execution]"
                                print(full_message)
                                # Potentially add the raw assistant message if needed
                                # chat_history.add_message(final_response_messages[0]) 
                        else:
                            full_message = "[No response from assistant after tool execution]"
                            print(full_message)

                    elif response[0].content:
                        full_message = str(response[0].content)
                        print(full_message)
                        chat_history.add_assistant_message(full_message)
                    else:
                        full_message = "[No content or tool call in response]"
                        print(full_message)
                        # Add the raw response to history if it's not a standard message or tool call
                        chat_history.add_message(response[0])

                else: # If it's not a list but has content (should ideally be handled by the list case too)
                    full_message = str(response.content)
                    print(full_message)
                    chat_history.add_assistant_message(full_message)
                
                logger.info(f"Assistant response: {full_message}")


            print("User > ", end="")

    except (KeyboardInterrupt, EOFError):
        print("\\nExiting application.")
        logger.info("Application exited by user.")
    finally:
        # Cleanup if necessary, e.g. if plugins have explicit close/dispose methods
        # For this example, our plugins don't require explicit cleanup beyond what Python's GC handles.
        logger.info("Application shutdown complete.")

if __name__ == "__main__":
    # Ensure the AZURE_OPENAI_DEPLOYMENT_NAME env var is used by SK Python for model_id/deployment_name
    # If users set AZURE_OPENAI_MODEL_ID (like in C#), we can alias it for convenience
    if not os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") and os.getenv("AZURE_OPENAI_MODEL_ID"):
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = os.getenv("AZURE_OPENAI_MODEL_ID")
        logger.info("Used AZURE_OPENAI_MODEL_ID as AZURE_OPENAI_DEPLOYMENT_NAME for SK Python compatibility.")
    
    asyncio.run(main()) 