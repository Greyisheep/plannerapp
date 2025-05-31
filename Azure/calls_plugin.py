import logging
import os
from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from twilio.rest import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class CallsPlugin:
    """Plugin to make voice calls using Twilio."""

    def __init__(self):
        load_dotenv() # Ensure environment variables are loaded
        self._account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self._auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._from_phone = os.getenv("TWILIO_FROM_PHONE")

        if not all([self._account_sid, self._auth_token, self._from_phone]):
            logger.error(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE) "
                "not found in environment variables for CallsPlugin."
            )
            self._client = None
        else:
            try:
                self._client = Client(self._account_sid, self._auth_token)
                logger.info("Twilio client for CallsPlugin initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client for CallsPlugin: {e}")
                self._client = None

    @kernel_function(
        description="Make a voice call using the Twilio API.",
        name="make_call"
    )
    async def make_call_async(
        self, 
        to_phone: Annotated[str, "The recipient's phone number in E.164 format (e.g., +1234567890)."], 
        # The C# version has a default voice_url. We replicate that here.
        # This URL points to a simple TwiML document that says "Hello from Twilio".
        voice_url: Annotated[str, "A URL pointing to TwiML instructions for the call. Defaults to a demo TwiML."] = "http://demo.twilio.com/docs/voice.xml"
    ) -> Annotated[str, "A message indicating success or failure of the call initiation."]:
        if not self._client:
            error_msg = "Twilio client not initialized for CallsPlugin. Check credentials."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"Attempting to make call to {to_phone} using TwiML at {voice_url}")
        try:
            call = self._client.calls.create(
                to=to_phone,
                from_=self._from_phone,
                url=voice_url
            )
            if call.sid:
                success_msg = f"Call initiated to {to_phone}. SID: {call.sid}"
                logger.info(success_msg)
                return success_msg
            else:
                error_msg = f"Failed to initiate call to {to_phone}. Twilio response: {call.error_message or 'Unknown error'}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error making call to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

# Example usage (for testing the plugin directly - requires Twilio credentials in .env):
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO) # Ensure logs are visible for direct test

    # --- Manual Test Setup ---
    # 1. Ensure .env file in this directory has your Twilio credentials (see SmsPlugin example)
    # 2. Set a recipient phone number (replace with a test number you own)
    test_to_phone = os.getenv("TEST_RECIPIENT_PHONE") # Or hardcode: "+1234567890"
    # Optional: A custom TwiML URL. Create one at TwiML Bin: https://www.twilio.com/console/runtime/twiml-bins
    # test_custom_twiml_url = "YOUR_CUSTOM_TWIML_URL_HERE"

    if not test_to_phone:
        print("Skipping CallsPlugin test: TEST_RECIPIENT_PHONE environment variable not set.")
        print("Please set it in your .env file to test this plugin.")
    else:
        plugin = CallsPlugin()
        if plugin._client: # Only run if client initialized
            async def run_call_test():
                print("--- Testing CallsPlugin ---")
                # Test making a call with default TwiML
                call_result_default = await plugin.make_call_async(to_phone=test_to_phone)
                print(f"Call (default TwiML) Result: {call_result_default}")

                # Example of using a custom TwiML (if you have one)
                # if test_custom_twiml_url:
                #     print("\n--- Testing with custom TwiML ---")
                #     call_result_custom = await plugin.make_call_async(
                #         to_phone=test_to_phone, 
                #         voice_url=test_custom_twiml_url
                #     )
                #     print(f"Call (custom TwiML) Result: {call_result_custom}")
                # else:
                #     print("\nSkipping custom TwiML test: test_custom_twiml_url not set.")
            
            asyncio.run(run_call_test())
        else:
            print("Skipping CallsPlugin test: Twilio client failed to initialize. Check .env credentials and logs.") 