import logging
import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class CallsTool:
    """Tool for making phone calls via Twilio."""

    def __init__(self):
        load_dotenv() # Ensure environment variables are loaded
        self._account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self._auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._from_phone = os.getenv("TWILIO_FROM_PHONE")
        self._client = None

        if not all([self._account_sid, self._auth_token, self._from_phone]):
            logger.warning(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE) "
                "not fully found in environment variables for CallsTool. Tool will not function."
            )
        else:
            try:
                self._client = Client(self._account_sid, self._auth_token)
                logger.info("Twilio client for CallsTool initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client for CallsTool: {e}")

    async def make_call(
        self, 
        to_phone: str,
        voice_url: str = "http://demo.twilio.com/docs/voice.xml"
    ) -> str:
        """Make a voice call using the Twilio API."""
        if not self._client:
            error_msg = "CallsTool: Twilio client not initialized. Check credentials and logs."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"CallsTool: Attempting to make call to {to_phone} using TwiML at {voice_url}")
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
                error_details = call.error_message if hasattr(call, 'error_message') and call.error_message else 'Unknown Twilio error'
                error_msg = f"Failed to initiate call to {to_phone}. Twilio response: {error_details}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error making call to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

# Example usage (for testing the tool directly - requires Twilio credentials in .env):
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    test_to_phone = os.getenv("TEST_RECIPIENT_PHONE")
    # Optional: A custom TwiML URL. Create one at TwiML Bin: https://www.twilio.com/console/runtime/twiml-bins
    # test_custom_twiml_url = "YOUR_CUSTOM_TWIML_URL_HERE"

    if not test_to_phone:
        print("Skipping CallsTool test: TEST_RECIPIENT_PHONE environment variable not set.")
    else:
        tool = CallsTool()
        if tool._client: 
            async def run_call_test():
                print("--- Testing CallsTool ---")
                call_result_default = await tool.make_call(to_phone=test_to_phone)
                print(f"Call (default TwiML) Result: {call_result_default}")
                
                # if test_custom_twiml_url:
                #     print("\n--- Testing with custom TwiML ---")
                #     call_result_custom = await tool.make_call(
                #         to_phone=test_to_phone, 
                #         voice_url=test_custom_twiml_url
                #     )
                #     print(f"Call (custom TwiML) Result: {call_result_custom}")
            
            asyncio.run(run_call_test())
        else:
            print("Skipping CallsTool test: Twilio client failed to initialize. Check .env credentials and logs.") 