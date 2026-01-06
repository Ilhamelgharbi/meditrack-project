#!/usr/bin/env python3
"""
Automated Reminder Scheduler
Runs continuously in the background to:
1. Generate reminders from schedules (daily)
2. Process and send due reminders (every 5 minutes)
3. Handle WhatsApp responses

Usage:
python automated_reminder_scheduler.py
"""

import sys
import os
import time
import logging
import schedule
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.db import get_db
from app.reminders.services import ReminderService
from app.reminders.models import ReminderSchedule, Reminder, ReminderStatusEnum
from app.whatsapp.reminder_sender import send_medication_reminder
from app.patients.models import Patient
from app.auth.models import User
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reminder_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedReminderScheduler:
    """Automated reminder system that runs continuously"""

    def __init__(self):
        self.db = next(get_db())
        self.service = ReminderService(self.db)
        self.last_generation_date = None

    def generate_scheduled_reminders(self):
        """Generate reminders from active schedules for the next 7 days"""
        logger.info("🔄 Generating scheduled reminders...")

        try:
            # Get all active reminder schedules
            active_schedules = self.db.query(ReminderSchedule).filter(
                ReminderSchedule.is_active == True
            ).all()

            if not active_schedules:
                logger.info("ℹ️ No active reminder schedules found.")
                return

            logger.info(f"Found {len(active_schedules)} active reminder schedules.")

            total_reminders_generated = 0

            for schedule in active_schedules:
                try:
                    # Generate reminders for the next 7 days
                    reminders = self.service.generate_reminders_for_schedule(
                        schedule.id, days_ahead=7
                    )

                    if reminders:
                        logger.info(f"✅ Schedule {schedule.id} (Patient {schedule.patient_id}): Generated {len(reminders)} reminders")
                        total_reminders_generated += len(reminders)
                    else:
                        logger.debug(f"ℹ️ Schedule {schedule.id} (Patient {schedule.patient_id}): No new reminders needed")

                except Exception as e:
                    logger.error(f"❌ Error generating reminders for schedule {schedule.id}: {e}")

            logger.info(f"✅ Generated {total_reminders_generated} total reminders")

        except Exception as e:
            logger.error(f"❌ Error in generate_scheduled_reminders: {e}")

    def process_due_reminders(self):
        """Process and send due reminders"""
        logger.info("📤 Processing due reminders...")

        try:
            now = datetime.now()
            yesterday = now - timedelta(days=1)

            # Get pending reminders that are due
            due_reminders = self.db.query(Reminder).filter(
                Reminder.status == ReminderStatusEnum.pending,
                Reminder.scheduled_time <= now,
                Reminder.scheduled_time >= yesterday
            ).all()

            if not due_reminders:
                logger.debug("ℹ️ No due reminders to process")
                return

            logger.info(f"Found {len(due_reminders)} due reminders to process")

            processed_count = 0
            failed_count = 0

            for reminder in due_reminders:
                try:
                    success = self.send_reminder_notification(reminder)
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                        # Increment retry count
                        reminder.retry_count += 1
                        if reminder.retry_count >= reminder.max_retries:
                            reminder.status = ReminderStatusEnum.failed
                        self.db.commit()

                except Exception as e:
                    logger.error(f"❌ Error processing reminder {reminder.id}: {e}")
                    failed_count += 1

            logger.info(f"✅ Processed: {processed_count}, Failed: {failed_count}")

        except Exception as e:
            logger.error(f"❌ Error in process_due_reminders: {e}")

    def send_reminder_notification(self, reminder: Reminder) -> bool:
        """Send WhatsApp notification for a reminder"""
        try:
            # Get patient and user info
            patient = self.db.query(Patient).filter(
                Patient.user_id == reminder.patient_id
            ).first()

            if not patient:
                logger.error(f"No patient profile found for user_id: {reminder.patient_id}")
                return False

            user = self.db.query(User).filter(User.id == reminder.patient_id).first()
            if not user or not user.phone:
                logger.error(f"No user or phone found for user_id: {reminder.patient_id}")
                return False

            # Get medication info
            medication_name = reminder.patient_medication.medication.name if reminder.patient_medication else "medication"
            dosage = reminder.patient_medication.dosage if reminder.patient_medication else None

            # Format date and time
            scheduled_time = reminder.scheduled_time
            date_str = scheduled_time.strftime("%m/%d")
            time_str = scheduled_time.strftime("%I:%M%p").lower()

            # Send WhatsApp message
            result = send_medication_reminder(
                to_phone=user.phone,
                medication_name=medication_name,
                date=date_str,
                time=time_str,
                dosage=dosage
            )

            if result.get('success'):
                # Mark reminder as sent
                reminder.status = ReminderStatusEnum.sent
                reminder.sent_at = datetime.now()
                reminder.twilio_message_sid = result.get('message_sid')
                self.db.commit()
                logger.info(f"✅ Sent reminder {reminder.id} to {user.phone}")
                return True
            else:
                logger.error(f"❌ Failed to send reminder {reminder.id}: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending reminder {reminder.id}: {e}")
            return False

    def check_daily_generation(self):
        """Check if we need to run daily reminder generation"""
        today = datetime.now().date()

        if self.last_generation_date != today:
            logger.info("📅 Running daily reminder generation...")
            self.generate_scheduled_reminders()
            self.last_generation_date = today

    def run(self):
        """Run the automated scheduler continuously"""
        logger.info("🚀 Starting Automated Reminder Scheduler...")

        # Schedule tasks
        schedule.every().day.at("00:01").do(self.generate_scheduled_reminders)  # Daily at 12:01 AM
        schedule.every(5).minutes.do(self.process_due_reminders)  # Every 5 minutes
        schedule.every().hour.do(self.check_daily_generation)  # Hourly check for daily generation

        # Initial generation
        self.check_daily_generation()

        logger.info("✅ Scheduler started. Running continuously...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
        finally:
            self.db.close()


def main():
    """Main entry point"""
    scheduler = AutomatedReminderScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()