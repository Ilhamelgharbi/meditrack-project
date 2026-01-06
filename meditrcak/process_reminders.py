#!/usr/bin/env python3
"""
Reminder Processing Script
This script should be run periodically (e.g., every 5 minutes) to process pending reminders
and send notifications to patients when their medication time arrives.

Usage:
- As a cron job: */5 * * * * /path/to/venv/bin/python /path/to/process_reminders.py
- Manual run: python process_reminders.py
- For testing: python process_reminders.py --dry-run
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.db import get_db
from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum
from app.patients.models import Patient
from app.auth.models import User
from app.whatsapp.reminder_sender import send_medication_reminder
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReminderProcessor:
    """Processes pending reminders and sends notifications"""

    def __init__(self, db: Session, dry_run: bool = False):
        self.db = db
        self.dry_run = dry_run

    def get_due_reminders(self) -> List[Reminder]:
        """Get reminders that are due to be sent"""
        now = datetime.now()

        # Get reminders that are:
        # 1. Pending status
        # 2. Scheduled time is now or in the past
        # 3. Within the last 24 hours (to avoid processing very old reminders)
        cutoff_time = now - timedelta(hours=24)

        due_reminders = self.db.query(Reminder).filter(
            Reminder.status == ReminderStatusEnum.pending,
            Reminder.scheduled_time <= now,
            Reminder.scheduled_time >= cutoff_time
        ).all()

        return due_reminders

    def send_whatsapp_reminder(self, reminder: Reminder) -> bool:
        """Send WhatsApp reminder using Twilio Content API (Templates)"""
        try:
            # Get patient contact info
            patient = self.db.query(Patient).filter(
                Patient.user_id == reminder.patient_id
            ).first()

            if not patient:
                logger.error(f"No patient profile found for user_id: {reminder.patient_id}")
                return False

            # Get user phone number
            user = self.db.query(User).filter(User.id == reminder.patient_id).first()
            if not user or not user.phone:
                logger.error(f"No user or phone found for user_id: {reminder.patient_id}")
                return False

            # Extract medication info
            medication_name = reminder.patient_medication.medication.name if reminder.patient_medication else "medication"
            dosage = reminder.patient_medication.dosage if reminder.patient_medication else None

            # Format date and time
            scheduled_time = reminder.scheduled_time
            date_str = scheduled_time.strftime("%m/%d")  # e.g., "12/20"
            time_str = scheduled_time.strftime("%I:%M%p").lower()  # e.g., "02:30pm"

            if self.dry_run:
                logger.info(f"[DRY RUN] Would send WhatsApp template reminder to {user.phone}")
                logger.info(f"[DRY RUN] Medication: {medication_name}, Date: {date_str}, Time: {time_str}")
                return True

            # Send template-based reminder
            result = send_medication_reminder(
                to_phone=user.phone,
                medication_name=medication_name,
                date=date_str,
                time=time_str,
                dosage=dosage
            )

            if result["success"]:
                logger.info(f"WhatsApp reminder sent successfully to {user.phone}. SID: {result.get('message_sid')}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp reminder to {user.phone}: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp reminder {reminder.id}: {e}")
            return False

    def process_reminder(self, reminder: Reminder) -> bool:
        """Process a single reminder"""
        try:
            success = False

            if reminder.channel == ReminderChannelEnum.whatsapp:
                success = self.send_whatsapp_reminder(reminder)
            elif reminder.channel == ReminderChannelEnum.sms:
                # TODO: Implement SMS sending
                logger.warning(f"SMS channel not implemented yet for reminder {reminder.id}")
                success = False
            else:
                logger.warning(f"Unknown channel {reminder.channel} for reminder {reminder.id}")
                success = False

            if success:
                # Update reminder status
                if not self.dry_run:
                    reminder.status = ReminderStatusEnum.sent
                    reminder.sent_at = datetime.now()
                    self.db.commit()
                logger.info(f"Reminder {reminder.id} processed successfully")
                return True
            else:
                # Mark as failed and increment retry count
                if not self.dry_run:
                    reminder.retry_count = (reminder.retry_count or 0) + 1
                    if reminder.retry_count >= (reminder.max_retries or 3):
                        reminder.status = ReminderStatusEnum.failed
                    self.db.commit()
                logger.error(f"Failed to process reminder {reminder.id}")
                return False

        except Exception as e:
            logger.error(f"Error processing reminder {reminder.id}: {e}")
            return False

    def process_all_due_reminders(self) -> dict:
        """Process all due reminders"""
        due_reminders = self.get_due_reminders()
        logger.info(f"Found {len(due_reminders)} due reminders to process")

        results = {
            'total': len(due_reminders),
            'processed': 0,
            'failed': 0
        }

        for reminder in due_reminders:
            if self.process_reminder(reminder):
                results['processed'] += 1
            else:
                results['failed'] += 1

        logger.info(f"Processing complete: {results['processed']} processed, {results['failed']} failed")
        return results


def main():
    parser = argparse.ArgumentParser(description='Process medication reminders')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually sending')
    args = parser.parse_args()

    db = next(get_db())
    try:
        processor = ReminderProcessor(db, dry_run=args.dry_run)
        results = processor.process_all_due_reminders()

        if args.dry_run:
            print(f"\nDRY RUN RESULTS:")
        else:
            print(f"\nPROCESSING RESULTS:")

        print(f"Total due reminders: {results['total']}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Failed: {results['failed']}")

    except Exception as e:
        logger.error(f"Error in reminder processing: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()