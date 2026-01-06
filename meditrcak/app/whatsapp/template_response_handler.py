"""
WhatsApp Template Response Handler
Handles responses to WhatsApp template messages (like medication reminders).
When users reply to templates, those messages come through the normal webhook.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.adherence.models import MedicationLog, AdherenceStats
from app.adherence.services import AdherenceService
from app.patients.models import Patient
from app.auth.models import User
from app.reminders.models import Reminder, ReminderStatusEnum

logger = logging.getLogger(__name__)


class TemplateResponseHandler:
    """Handles WhatsApp template responses"""

    def __init__(self, db: Session):
        self.db = db

    def handle_reminder_response(self, user_phone: str, message_body: str) -> Dict[str, Any]:
        """
        Handle response to a medication reminder template.

        Args:
            user_phone: Phone number that sent the response
            message_body: The response message (e.g., "YES", "TAKEN", "SKIP")

        Returns:
            Dict with processing results
        """
        try:
            # Clean the phone number
            phone = user_phone.replace("whatsapp:", "").strip()

            # Find the user
            user = self.db.query(User).filter(User.phone == phone).first()
            if not user:
                logger.warning(f"No user found for phone: {phone}")
                return {"success": False, "error": "User not found"}

            # Normalize the response
            response = message_body.strip().upper()

            # Define positive responses (medication taken)
            positive_responses = ["YES", "TAKEN", "DONE", "TOOK IT", "CONFIRMED", "✓", "✅"]

            # Define skip responses
            skip_responses = ["SKIP", "LATER", "SNOOZE", "REMIND LATER"]

            # Define negative responses (not taken)
            negative_responses = ["NO", "MISSED", "FORGOT", "CAN'T", "WON'T"]

            action_taken = None
            notes = f"WhatsApp response: {message_body}"

            if response in positive_responses:
                action_taken = "taken"
                logger.info(f"User {user.id} confirmed medication taken via WhatsApp")
            elif response in skip_responses:
                action_taken = "skipped"
                logger.info(f"User {user.id} skipped medication via WhatsApp")
            elif response in negative_responses:
                action_taken = "missed"
                logger.info(f"User {user.id} reported missed medication via WhatsApp")
            else:
                # Unknown response - could be a question or other message
                logger.info(f"Unknown WhatsApp response from user {user.id}: {message_body}")
                return {
                    "success": True,
                    "action": "unknown_response",
                    "message": "Response logged but not recognized as medication action"
                }

            # Find the most recent pending reminder for this user (within last 24 hours)
            yesterday = datetime.now() - timedelta(hours=24)
            recent_reminder = self.db.query(Reminder).filter(
                Reminder.patient_id == user.id,
                Reminder.status == ReminderStatusEnum.sent,
                Reminder.scheduled_time >= yesterday
            ).order_by(Reminder.scheduled_time.desc()).first()

            if recent_reminder:
                # Log the medication action
                success = self._log_medication_action(
                    user_id=user.id,
                    reminder=recent_reminder,
                    action=action_taken,
                    notes=notes
                )

                if success:
                    # Update reminder status
                    if action_taken == "taken":
                        recent_reminder.status = ReminderStatusEnum.completed
                    elif action_taken == "skipped":
                        recent_reminder.status = ReminderStatusEnum.skipped

                    self.db.commit()

                    return {
                        "success": True,
                        "action": action_taken,
                        "reminder_id": recent_reminder.id,
                        "medication": recent_reminder.patient_medication.medication.name if recent_reminder.patient_medication else "Unknown"
                    }
                else:
                    return {"success": False, "error": "Failed to log medication action"}
            else:
                # No recent reminder found - still log the action if it's positive
                if action_taken == "taken":
                    # Try to find any active medication for this user
                    patient = self.db.query(Patient).filter(Patient.user_id == user.id).first()
                    if patient and patient.current_medications:
                        # Log a general medication taken action
                        success = self._log_general_medication_action(
                            user_id=user.id,
                            action=action_taken,
                            notes=notes
                        )
                        if success:
                            return {
                                "success": True,
                                "action": action_taken,
                                "message": "Medication action logged (no specific reminder found)"
                            }

                logger.warning(f"No recent reminder found for user {user.id} response: {message_body}")
                return {
                    "success": False,
                    "error": "No recent reminder found to associate with this response"
                }

        except Exception as e:
            logger.error(f"Error handling WhatsApp template response: {e}")
            return {"success": False, "error": str(e)}

    def _log_medication_action(self, user_id: int, reminder: Reminder, action: str, notes: str) -> bool:
        """Log a medication action associated with a specific reminder"""
        try:
            # Create medication log entry
            log_entry = MedicationLog(
                user_id=user_id,
                patient_medication_id=reminder.patient_medication_id,
                scheduled_time=reminder.scheduled_time,
                actual_time=datetime.now(),
                status=action,  # "taken", "missed", "skipped"
                notes=notes,
                reminder_id=reminder.id
            )

            self.db.add(log_entry)

            # Update adherence stats
            AdherenceService._recalculate_stats(self.db, user_id, reminder.patient_medication_id)

            self.db.commit()
            logger.info(f"Logged medication action: {action} for user {user_id}, reminder {reminder.id}")
            return True

        except Exception as e:
            logger.error(f"Error logging medication action: {e}")
            self.db.rollback()
            return False

    def _log_general_medication_action(self, user_id: int, action: str, notes: str) -> bool:
        """Log a general medication action when no specific reminder is found"""
        try:
            # This is a simplified version - in a real app you'd want to be more specific
            log_entry = MedicationLog(
                user_id=user_id,
                actual_time=datetime.now(),
                status=action,
                notes=notes
            )

            self.db.add(log_entry)
            self.db.commit()
            logger.info(f"Logged general medication action: {action} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error logging general medication action: {e}")
            self.db.rollback()
            return False

    def is_reminder_response(self, message_body: str) -> bool:
        """
        Check if a message appears to be a response to a reminder template.
        This helps distinguish reminder responses from general chat messages.
        """
        response = message_body.strip().upper()

        reminder_keywords = [
            "YES", "NO", "TAKEN", "DONE", "SKIP", "LATER", "SNOOZE",
            "MISSED", "FORGOT", "CONFIRMED", "✓", "✅", "X"
        ]

        return any(keyword in response for keyword in reminder_keywords)


# Convenience function for use in webhook
def handle_whatsapp_template_response(user_phone: str, message_body: str, db: Session) -> Dict[str, Any]:
    """
    Convenience function to handle WhatsApp template responses.
    Use this in your webhook handler.
    """
    handler = TemplateResponseHandler(db)
    return handler.handle_reminder_response(user_phone, message_body)