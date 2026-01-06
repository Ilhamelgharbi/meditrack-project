# app/agent/tools/patients/reminder_tools.py
"""
Patient Tools for Reminder Management.

Mirrors React reminder system:
- View daily/weekly reminders
- Manage reminder interactions
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.database.db import get_db
from app.reminders.services import ReminderService
from app.reminders.models import ReminderChannelEnum, ReminderStatusEnum
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class Context(TypedDict):
    """Context passed to tools from the agent runtime."""
    user_id: str
    token: str
    role: str


def _get_db_session() -> Session:
    """Get a database session."""
    return next(get_db())


# ============================================================================
# PATIENT REMINDER TOOLS
# ============================================================================

@tool("get_my_reminders", description="Get my medication reminders for today or a specific date.")
def get_my_reminders(
    runtime: ToolRuntime[Context],
    date: Optional[str] = None,
    include_completed: bool = False
) -> str:
    """
    Get my medication reminders for a specific date.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
        include_completed: Whether to include completed reminders

    Returns:
        List of reminders with times and medications
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Use ReminderService
        service = ReminderService(db)

        # Parse date or use today
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return f"Invalid date format. Please use YYYY-MM-DD format."
        else:
            target_date = datetime.now().date()

        # Get reminders for the date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        reminders = service.get_patient_reminders(
            patient_id=user_id,
            start_date=start_datetime,
            end_date=end_datetime
        )

        # Filter by status if not including completed
        if not include_completed:
            from app.reminders.models import ReminderStatusEnum
            reminders = [r for r in reminders if r.status in [
                ReminderStatusEnum.pending,
                ReminderStatusEnum.sent,
                ReminderStatusEnum.delivered
            ]]

        if not reminders:
            status_msg = " (including completed)" if include_completed else ""
            return f"No medication reminders found for {target_date}{status_msg}."

        # Format response - cleaner format for agent consumption
        if len(reminders) == 1:
            reminder = reminders[0]
            pm = reminder.patient_medication
            time_str = reminder.scheduled_time.strftime("%I:%M %p")
            med_name = pm.medication.name if pm.medication else "Unknown medication"
            dosage = pm.dosage or "Dosage not specified"
            return f"You have a reminder for {med_name} ({dosage}) at {time_str}."
        else:
            # Multiple reminders
            reminder_list = []
            for reminder in reminders:
                pm = reminder.patient_medication
                time_str = reminder.scheduled_time.strftime("%I:%M %p")
                med_name = pm.medication.name if pm.medication else "Unknown medication"
                dosage = pm.dosage or "Dosage not specified"
                reminder_list.append(f"{med_name} ({dosage}) at {time_str}")
            
            return f"You have {len(reminders)} reminders today: {', '.join(reminder_list)}."

    except Exception as e:
        logger.error(f"Error getting reminders for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving reminders: {str(e)}"
    finally:
        db.close()


@tool("set_medication_reminder", description="Set up automatic medication reminders for a medication based on its schedule.")
def set_medication_reminder(
    runtime: ToolRuntime[Context],
    medication_name: str
) -> str:
    """
    Set up automatic medication reminders for a medication based on its prescribed schedule.

    This creates a reminder schedule that will automatically generate reminders
    according to the medication's frequency and times per day.

    Args:
        medication_name: The name of the medication (e.g., "Amlodipine", "Metformin")

    Returns:
        Confirmation of reminder schedule creation
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Use ReminderService
        service = ReminderService(db)

        # Find the patient medication by name
        from app.medications.models import PatientMedication, Medication
        from sqlalchemy import func
        patient_med = db.query(PatientMedication).join(PatientMedication.medication).filter(
            PatientMedication.patient_id == user_id,
            PatientMedication.status == "active",
            func.lower(Medication.name).like(f"%{medication_name.lower()}%")
        ).first()

        if not patient_med:
            return f"Medication '{medication_name}' not found in your active medications. Please check the spelling or use 'get_my_medications' to see your current medications."

        # Check if reminder schedule already exists
        from app.reminders.models import ReminderSchedule
        existing_schedule = db.query(ReminderSchedule).filter(
            ReminderSchedule.patient_medication_id == patient_med.id
        ).first()

        if existing_schedule:
            return f"Reminder schedule already exists for {patient_med.medication.name}. Automatic reminders are already set up for this medication."

        # Determine reminder times based on times_per_day
        times_per_day = patient_med.times_per_day or 1

        if times_per_day == 1:
            # Once daily - assume evening (8 PM)
            reminder_times = ["20:00"]
        elif times_per_day == 2:
            # Twice daily - morning and evening
            reminder_times = ["08:00", "20:00"]
        elif times_per_day == 3:
            # Three times daily - morning, afternoon, evening
            reminder_times = ["08:00", "14:00", "20:00"]
        elif times_per_day == 4:
            # Four times daily - every 6 hours
            reminder_times = ["06:00", "12:00", "18:00", "00:00"]
        else:
            # Default to once daily
            reminder_times = ["20:00"]

        # Create reminder schedule
        from app.reminders.schemas import ReminderScheduleCreate, ReminderFrequency
        schedule_data = ReminderScheduleCreate(
            patient_medication_id=patient_med.id,
            frequency=ReminderFrequency.daily,
            reminder_times=reminder_times,
            advance_minutes=15,  # 15 minutes before dose
            channel_whatsapp=True,
            channel_sms=False,
            channel_push=True,
            channel_email=False,
            auto_skip_if_taken=True,
            escalate_if_missed=True,
            escalate_delay_minutes=30,
            quiet_hours_enabled=False,
            start_date=datetime.now(),
            end_date=patient_med.end_date  # Use medication end date if set
        )

        # Create the schedule
        schedule = service.create_reminder_schedule(
            patient_id=user_id,
            schedule_data=schedule_data
        )

        # Generate initial reminders for the next 7 days
        initial_reminders = service.generate_reminders_for_schedule(
            schedule.id,
            days_ahead=7
        )

        # Format response
        times_str = ", ".join([f"{t} daily" for t in reminder_times])
        response = f"✅ Successfully set up automatic reminders for {patient_med.medication.name} ({patient_med.dosage}).\n"
        response += f"📅 Schedule: {times_str}\n"
        response += f"⏰ Advance notice: 15 minutes before each dose\n"
        response += f"📱 Notifications: WhatsApp + Push\n"
        response += f"🔄 Generated {len(initial_reminders)} initial reminders for the next 7 days."

        logger.info(f"Reminder schedule created for user {user_id}: medication {medication_name}, {len(initial_reminders)} reminders generated")
        return response

    except Exception as e:
        logger.error(f"Error setting up reminder schedule for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error setting up reminder schedule: {str(e)}"
    finally:
        db.close()


@tool("get_upcoming_reminders", description="Get medication reminders for the next few hours.")
def get_upcoming_reminders(
    runtime: ToolRuntime[Context],
    hours_ahead: int = 4
) -> str:
    """
    Get reminders for medications I need to take soon.

    Args:
        hours_ahead: Number of hours to look ahead

    Returns:
        List of upcoming medication reminders
    """
    # TODO: Implement upcoming reminders retrieval
    return f"Patient upcoming reminders tool - placeholder for {hours_ahead} hours ahead"


@tool("snooze_reminder", description="Postpone a reminder for a specified time.")
def snooze_reminder(
    runtime: ToolRuntime[Context],
    reminder_id: int,
    minutes: int = 15
) -> str:
    """
    Snooze a medication reminder.

    Args:
        reminder_id: The ID of the reminder to snooze
        minutes: Number of minutes to postpone

    Returns:
        Confirmation of reminder snooze
    """
    # TODO: Implement reminder snoozing
    return f"Patient reminder snooze tool - placeholder for reminder {reminder_id}, {minutes} minutes"


@tool("complete_reminder", description="Mark a reminder as completed.")
def complete_reminder(
    runtime: ToolRuntime[Context],
    reminder_id: int
) -> str:
    """
    Mark a medication reminder as completed.

    Args:
        reminder_id: The ID of the reminder to complete

    Returns:
        Confirmation of reminder completion
    """
    # TODO: Implement reminder completion
    return f"Patient reminder completion tool - placeholder for reminder {reminder_id}"


@tool("get_reminder_history", description="Get history of past reminders.")
def get_reminder_history(
    runtime: ToolRuntime[Context],
    days: int = 7
) -> str:
    """
    Get history of past medication reminders.

    Args:
        days: Number of days to look back

    Returns:
        History of past reminders and their status
    """
    # TODO: Implement reminder history retrieval
    return f"Patient reminder history tool - placeholder for {days} days"