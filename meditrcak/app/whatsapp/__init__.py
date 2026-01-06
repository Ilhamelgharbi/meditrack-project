"""
WhatsApp integration package for MediTrack AI
Handles WhatsApp messaging, templates, and responses.
"""

from .reminder_sender import (
    send_medication_reminder,
    send_custom_reminder_template,
    send_morning_reminder,
    send_evening_reminder,
    send_specific_time_reminder
)

from .template_response_handler import (
    TemplateResponseHandler,
    handle_whatsapp_template_response
)

__all__ = [
    # Reminder sending
    "send_medication_reminder",
    "send_custom_reminder_template",
    "send_morning_reminder",
    "send_evening_reminder",
    "send_specific_time_reminder",

    # Response handling
    "TemplateResponseHandler",
    "handle_whatsapp_template_response"
]