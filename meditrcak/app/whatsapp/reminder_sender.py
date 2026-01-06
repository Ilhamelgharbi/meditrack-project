"""
WhatsApp Reminder Sender using Twilio Content API (Templates)
This is the correct way to send medication reminders via WhatsApp.
Templates are required for proactive messages like reminders.
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Twilio Configuration from settings
ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_FROM = settings.TWILIO_WHATSAPP_NUMBER

# WhatsApp Template SIDs (you need to create these in Twilio Console)
# For sandbox testing, you might need to use free text instead of templates
REMINDER_TEMPLATE_SID = "HXb5b62575e6e4ff6129ad7c8efe1f983e"  # Production template

# Sandbox mode detection (check if using Twilio sandbox number)
IS_SANDBOX = TWILIO_FROM == "whatsapp:+14155238886" or not ACCOUNT_SID or not AUTH_TOKEN

# Initialize Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_medication_reminder(
    to_phone: str,
    medication_name: str,
    date: str,
    time: str,
    dosage: Optional[str] = None,
    template_sid: str = REMINDER_TEMPLATE_SID
) -> Dict[str, Any]:
    """
    Send medication reminder using WhatsApp.

    In SANDBOX mode: Uses free text (allowed for testing)
    In PRODUCTION mode: Uses templates (required by WhatsApp)

    Args:
        to_phone: Recipient phone number (without whatsapp: prefix)
        medication_name: Name of the medication
        date: Date string (e.g., "12/1", "Dec 1")
        time: Time string (e.g., "3pm", "15:00")
        dosage: Optional dosage information
        template_sid: WhatsApp template SID (production only)

    Returns:
        Dict with success status and message details
    """
    try:
        # Format phone number with whatsapp: prefix
        to_whatsapp = f"whatsapp:{to_phone}"

        logger.info(f"Sending WhatsApp reminder to {to_phone} (Sandbox: {IS_SANDBOX})")

        if IS_SANDBOX:
            # SANDBOX MODE: Use free text (allowed for testing)
            message_body = f"💊 Medication Reminder\n\nIt's time to take your {medication_name}"
            if dosage:
                message_body += f" ({dosage})"
            message_body += f" on {date} at {time}.\n\nReply YES once taken."

            logger.info(f"Sandbox mode: Sending free text reminder")

            message = client.messages.create(
                from_=TWILIO_FROM,
                to=to_whatsapp,
                body=message_body
            )

            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_phone,
                "mode": "sandbox",
                "body": message_body
            }
        else:
            # PRODUCTION MODE: Use templates (required by WhatsApp)
            # Prepare template variables
            content_variables = {
                "1": date,
                "2": time
            }

            # Add medication name and dosage if provided (depending on template)
            if medication_name:
                content_variables["3"] = medication_name
            if dosage:
                content_variables["4"] = dosage

            logger.info(f"Production mode: Sending template {template_sid}")

            message = client.messages.create(
                from_=TWILIO_FROM,
                to=to_whatsapp,
                content_sid=template_sid,
                content_variables=content_variables
            )

            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_phone,
                "template_sid": template_sid,
                "variables": content_variables,
                "mode": "production"
            }

    except TwilioRestException as e:
        logger.error(f"Twilio error sending WhatsApp reminder: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": e.code,
            "to": to_phone,
            "mode": "sandbox" if IS_SANDBOX else "production"
        }
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp reminder: {e}")
        return {
            "success": False,
            "error": str(e),
            "to": to_phone,
            "mode": "sandbox" if IS_SANDBOX else "production"
        }


def send_custom_reminder_template(
    to_phone: str,
    template_sid: str,
    variables: Dict[str, str]
) -> Dict[str, Any]:
    """
    Send custom WhatsApp template message.

    Args:
        to_phone: Recipient phone number (without whatsapp: prefix)
        template_sid: WhatsApp template SID
        variables: Dictionary of template variables (e.g., {"1": "value1", "2": "value2"})

    Returns:
        Dict with success status and message details
    """
    try:
        to_whatsapp = f"whatsapp:{to_phone}"

        logger.info(f"Sending custom WhatsApp template to {to_phone}")
        logger.info(f"Template: {template_sid}, Variables: {variables}")

        message = client.messages.create(
            from_=TWILIO_FROM,
            to=to_whatsapp,
            content_sid=template_sid,
            content_variables=variables
        )

        logger.info(f"Custom WhatsApp template sent successfully. SID: {message.sid}")

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
            "to": to_phone,
            "template_sid": template_sid,
            "variables": variables
        }

    except TwilioRestException as e:
        logger.error(f"Twilio error sending custom WhatsApp template: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": e.code,
            "to": to_phone
        }
    except Exception as e:
        logger.error(f"Unexpected error sending custom WhatsApp template: {e}")
        return {
            "success": False,
            "error": str(e),
            "to": to_phone
        }


# Convenience functions for different reminder types
def send_morning_reminder(to_phone: str, medication_name: str, dosage: str = None) -> Dict[str, Any]:
    """Send morning medication reminder"""
    today = datetime.now().strftime("%m/%d")
    return send_medication_reminder(
        to_phone=to_phone,
        medication_name=medication_name,
        date=today,
        time="morning",
        dosage=dosage
    )


def send_evening_reminder(to_phone: str, medication_name: str, dosage: str = None) -> Dict[str, Any]:
    """Send evening medication reminder"""
    today = datetime.now().strftime("%m/%d")
    return send_medication_reminder(
        to_phone=to_phone,
        medication_name=medication_name,
        date=today,
        time="evening",
        dosage=dosage
    )


def send_specific_time_reminder(to_phone: str, medication_name: str, time: str, dosage: str = None) -> Dict[str, Any]:
    """Send reminder for specific time"""
    today = datetime.now().strftime("%m/%d")
    return send_medication_reminder(
        to_phone=to_phone,
        medication_name=medication_name,
        date=today,
        time=time,
        dosage=dosage
    )


# Test function
def test_reminder():
    """Test the reminder functionality"""
    # This would be a test phone number you have access to
    test_phone = "+212619169650"  # Replace with your test number

    result = send_medication_reminder(
        to_phone=test_phone,
        medication_name="Aspirin",
        date="12/20",
        time="2pm",
        dosage="100mg"
    )

    print("Test result:", result)
    return result


if __name__ == "__main__":
    # Run test if executed directly
    test_reminder()