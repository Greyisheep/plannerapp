import logging
import os
from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from twilio.rest import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SmsPlugin:
    """Plugin to send SMS and MMS messages using Twilio."""

    def __init__(self):
        load_dotenv() # Ensure environment variables are loaded
        self._account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self._auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._from_phone = os.getenv("TWILIO_FROM_PHONE")

        if not all([self._account_sid, self._auth_token, self._from_phone]):
            logger.error(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE) "
                "not found in environment variables."
            )
            # You might raise an error here or disable the plugin functionality
            self._client = None
        else:
            try:
                self._client = Client(self._account_sid, self._auth_token)
                logger.info("Twilio client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self._client = None

    @kernel_function(
        description="Send an SMS text message using the Twilio API.",
        name="send_sms"
    )
    async def send_sms_async(
        self, 
        to_phone: Annotated[str, "The recipient's phone number in E.164 format (e.g., +1234567890)."], 
        message: Annotated[str, "The text message to send."]
    ) -> Annotated[str, "A message indicating success or failure of the SMS sending."]:
        if not self._client:
            error_msg = "Twilio client not initialized. Check credentials."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"Attempting to send SMS to {to_phone} with message: '{message[:30]}...'")
        try:
            twilio_message = self._client.messages.create(
                to=to_phone,
                from_=self._from_phone,
                body=message
            )
            if twilio_message.sid:
                success_msg = f"SMS sent to {to_phone}: '{message}'. SID: {twilio_message.sid}"
                logger.info(success_msg)
                return success_msg
            else:
                # This case might indicate an issue not caught by an exception, e.g. validation error from Twilio
                error_msg = f"Failed to send SMS to {to_phone}. Twilio response: {twilio_message.error_message or 'Unknown error'}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Error sending SMS to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

    @kernel_function(
        description="Send an MMS message with media using the Twilio API.",
        name="send_mms"
    )
    async def send_mms_async(
        self, 
        to_phone: Annotated[str, "The recipient's phone number in E.164 format (e.g., +1234567890)."], 
        message: Annotated[str, "The text message to send with the media."], 
        media_url: Annotated[str, "A publicly accessible URL of the media to send (e.g., a .jpg, .png, .gif file)."]
    ) -> Annotated[str, "A message indicating success or failure of the MMS sending."]:
        if not self._client:
            error_msg = "Twilio client not initialized. Check credentials."
            logger.error(error_msg)
            return error_msg

        logger.info(f"Attempting to send MMS to {to_phone} with message: '{message[:30]}...' and media: {media_url}")
        try:
            twilio_message = self._client.messages.create(
                to=to_phone,
                from_=self._from_phone,
                body=message,
                media_url=[media_url]  # Must be a list of URLs
            )
            if twilio_message.sid:
                success_msg = f"MMS sent to {to_phone}: '{message}' with media: {media_url}. SID: {twilio_message.sid}"
                logger.info(success_msg)
                return success_msg
            else:
                error_msg = f"Failed to send MMS to {to_phone}. Twilio response: {twilio_message.error_message or 'Unknown error'}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error sending MMS to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

# Example usage (for testing the plugin directly - requires Twilio credentials in .env):
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO) # Ensure logs are visible for direct test

    # --- Manual Test Setup ---
    # 1. Create a .env file in this directory with your Twilio credentials:
    #    TWILIO_ACCOUNT_SID=your_account_sid
    #    TWILIO_AUTH_TOKEN=your_auth_token
    #    TWILIO_FROM_PHONE=your_twilio_phone_number
    # 2. Set a recipient phone number (replace with a test number you own)
    test_to_phone = os.getenv("TEST_RECIPIENT_PHONE") # Or hardcode: "+1234567890"
    test_media_url = "https://www.twilio.com/docs/static/img/icon-twilio.png" # Example public media

    if not test_to_phone:
        print("Skipping SMS/MMS plugin test: TEST_RECIPIENT_PHONE environment variable not set.")
        print("Please set it in your .env file to test this plugin.")
    else:
        plugin = SmsPlugin()
        if plugin._client: # Only run if client initialized
            async def run_tests():
                print("--- Testing SMSPlugin ---")
                # Test sending SMS
                sms_result = await plugin.send_sms_async(
                    to_phone=test_to_phone, 
                    message="Hello from Python Semantic Kernel SmsPlugin!"
                )
                print(f"SMS Send Result: {sms_result}")

                # Test sending MMS
                mms_result = await plugin.send_mms_async(
                    to_phone=test_to_phone, 
                    message="Hello with media from Python SK SmsPlugin!",
                    media_url=test_media_url
                )
                print(f"MMS Send Result: {mms_result}")
            
            asyncio.run(run_tests())
        else:
            print("Skipping SMS/MMS plugin test: Twilio client failed to initialize. Check .env credentials and logs.") 