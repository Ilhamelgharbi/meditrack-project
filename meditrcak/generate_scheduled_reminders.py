#!/usr/bin/env python3
"""
Background job to generate reminders from active reminder schedules.
This script should be run periodically (e.g., daily) to ensure upcoming reminders are created.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database.db import get_db
from app.reminders.services import ReminderService
from app.reminders.models import ReminderSchedule


def generate_scheduled_reminders():
    """Generate reminders for all active reminder schedules"""
    print(f"🔄 Starting reminder generation at {datetime.now()}")

    db = next(get_db())

    try:
        # Get all active reminder schedules
        active_schedules = db.query(ReminderSchedule).filter(
            ReminderSchedule.is_active == True
        ).all()

        if not active_schedules:
            print("❌ No active reminder schedules found.")
            return

        print(f"Found {len(active_schedules)} active reminder schedules.")

        service = ReminderService(db)
        total_reminders_generated = 0

        for schedule in active_schedules:
            try:
                # Generate reminders for the next 7 days
                reminders = service.generate_reminders_for_schedule(
                    schedule.id,
                    days_ahead=7
                )

                if reminders:
                    print(f"  ✅ Schedule {schedule.id} (Patient {schedule.patient_id}): Generated {len(reminders)} reminders")
                    total_reminders_generated += len(reminders)
                else:
                    print(f"  ℹ️  Schedule {schedule.id} (Patient {schedule.patient_id}): No new reminders needed")

            except Exception as e:
                print(f"  ❌ Error generating reminders for schedule {schedule.id}: {e}")

        print(f"🎉 Completed! Generated {total_reminders_generated} total reminders.")

    except Exception as e:
        print(f"❌ Error during reminder generation: {e}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    generate_scheduled_reminders()