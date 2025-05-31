import logging
import os
from twilio.rest import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SmsTool:
    """Tool for sending SMS and MMS messages via Twilio."""

    def __init__(self):
        load_dotenv() # Ensure environment variables are loaded
        self._account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self._auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._from_phone = os.getenv("TWILIO_FROM_PHONE")
        self._client = None

        if not all([self._account_sid, self._auth_token, self._from_phone]):
            logger.warning(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE) "
                "not fully found in environment variables for SmsTool. Tool will not function."
            )
        else:
            try:
                self._client = Client(self._account_sid, self._auth_token)
                logger.info("Twilio client for SmsTool initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client for SmsTool: {e}")

    async def send_sms(
        self, 
        to_phone: str,
        message: str
    ) -> str:
        """Send an SMS text message using the Twilio API."""
        if not self._client:
            error_msg = "SmsTool: Twilio client not initialized. Check credentials and logs."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"SmsTool: Attempting to send SMS to {to_phone} with message: '{message[:30]}...'")
        try:
            twilio_message = self._client.messages.create(
                to=to_phone,
                from_=self._from_phone,
                body=message
            )
            if twilio_message.sid:
                success_msg = f"SMS sent to {to_phone}. SID: {twilio_message.sid}"
                logger.info(success_msg)
                return success_msg
            else:
                # This case might indicate an issue not caught by an exception
                error_details = twilio_message.error_message if hasattr(twilio_message, 'error_message') and twilio_message.error_message else 'Unknown Twilio error'
                error_msg = f"Failed to send SMS to {to_phone}. Twilio response: {error_details}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error sending SMS to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

    async def send_mms(
        self, 
        to_phone: str,
        message: str,
        media_url: str
    ) -> str:
        """Send an MMS message with media using the Twilio API."""
        if not self._client:
            error_msg = "SmsTool: Twilio client not initialized. Check credentials and logs."
            logger.error(error_msg)
            return error_msg

        logger.info(f"SmsTool: Attempting to send MMS to {to_phone} with message: '{message[:30]}...' and media: {media_url}")
        try:
            twilio_message = self._client.messages.create(
                to=to_phone,
                from_=self._from_phone,
                body=message,
                media_url=[media_url]  # Must be a list of URLs
            )
            if twilio_message.sid:
                success_msg = f"MMS sent to {to_phone} with media {media_url}. SID: {twilio_message.sid}"
                logger.info(success_msg)
                return success_msg
            else:
                error_details = twilio_message.error_message if hasattr(twilio_message, 'error_message') and twilio_message.error_message else 'Unknown Twilio error'
                error_msg = f"Failed to send MMS to {to_phone}. Twilio response: {error_details}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error sending MMS to {to_phone}: {e}"
            logger.error(error_msg)
            return error_msg

# Example usage (for testing the tool directly - requires Twilio credentials in .env):
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    test_to_phone = os.getenv("TEST_RECIPIENT_PHONE")
    test_media_url = "https://www.twilio.com/docs/static/img/icon-twilio.png" 

    if not test_to_phone:
        print("Skipping SmsTool test: TEST_RECIPIENT_PHONE environment variable not set.")
    else:
        tool = SmsTool()
        if tool._client: 
            async def run_tests():
                print("--- Testing SmsTool ---")
                sms_result = await tool.send_sms(
                    to_phone=test_to_phone, 
                    message="Hello from ADK SmsTool!"
                )
                print(f"SMS Send Result: {sms_result}")

                mms_result = await tool.send_mms(
                    to_phone=test_to_phone, 
                    message="Hello with media from ADK SmsTool!",
                    media_url=test_media_url
                )
                print(f"MMS Send Result: {mms_result}")
            
            asyncio.run(run_tests())
        else:
            print("Skipping SmsTool test: Twilio client failed to initialize. Check .env credentials and logs.") 