# app/agent/tools/patients/scheduling_tools.py
"""
Patient Tools for Medication Scheduling.

Mirrors React scheduling logic:
- View daily/weekly schedules
- Manage medication timing
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.database.db import get_db
from app.reminders.models import ReminderSchedule, ReminderFrequencyEnum
from app.medications.models import PatientMedication
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
# PATIENT SCHEDULING TOOLS
# ============================================================================

@tool("get_my_schedule", description="Get my medication schedule for a specific date.")
def get_my_schedule(
    runtime: ToolRuntime[Context],
    date: Optional[str] = None
) -> str:
    """
    Get my complete medication schedule for a specific date.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)

    Returns:
        Daily medication schedule with times
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Parse date or use today
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return f"Invalid date format. Please use YYYY-MM-DD format."
        else:
            target_date = datetime.now().date()

        # Get active medications with their schedules
        medications = db.query(PatientMedication).filter(
            PatientMedication.patient_id == user_id,
            PatientMedication.status == "active"
        ).all()

        if not medications:
            return f"No active medications found for {target_date}."

        schedule_lines = [f"Your medication schedule for {target_date}:"]
        has_schedule = False

        for med in medications:
            med_name = med.medication.name if med.medication else "Unknown medication"
            dosage = med.dosage or "Dosage not specified"

            # Check if there's a reminder schedule
            if med.reminder_schedule and med.reminder_schedule.is_active:
                schedule = med.reminder_schedule
                if schedule.reminder_times:
                    has_schedule = True
                    schedule_lines.append(f"\n{med_name} ({dosage}):")
                    for time_str in schedule.reminder_times:
                        try:
                            # Parse time and format nicely
                            time_obj = datetime.strptime(time_str, "%H:%M").time()
                            time_formatted = time_obj.strftime("%I:%M %p")
                            schedule_lines.append(f"  • {time_formatted}")
                        except ValueError:
                            schedule_lines.append(f"  • {time_str} (invalid format)")
            else:
                # No schedule set up
                schedule_lines.append(f"\n{med_name} ({dosage}): No schedule configured")

        if not has_schedule:
            schedule_lines.append("\nNo medication schedules are currently set up.")
            schedule_lines.append("Use 'create_medication_schedule' to set up reminders for your medications.")

        response = "\n".join(schedule_lines)
        logger.info(f"Schedule retrieved for user {user_id}: {len(medications)} medications for {target_date}")
        return response

    except Exception as e:
        logger.error(f"Error getting schedule for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving medication schedule: {str(e)}"
    finally:
        db.close()


@tool("get_weekly_schedule", description="Get my medication schedule for the current week.")
def get_weekly_schedule(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my medication schedule for the entire week.

    Returns:
        Weekly medication schedule overview
    """
    # TODO: Implement weekly schedule retrieval
    return "Patient weekly schedule tool - placeholder implementation"


@tool("reschedule_medication", description="Change the timing of a medication.")
def reschedule_medication(
    runtime: ToolRuntime[Context],
    medication_id: int,
    new_times: List[str]
) -> str:
    """
    Reschedule a medication to different times.

    Args:
        medication_id: The ID of the patient_medication
        new_times: List of new times in HH:MM format

    Returns:
        Confirmation of schedule change
    """
    # TODO: Implement medication rescheduling
    return f"Patient reschedule tool - placeholder for medication {medication_id}"


@tool("get_schedule_conflicts", description="Check for conflicts in my medication schedule.")
def get_schedule_conflicts(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Check for overlapping or conflicting medication times.

    Returns:
        List of scheduling conflicts and suggestions
    """
    # TODO: Implement conflict detection
    return "Patient schedule conflicts tool - placeholder implementation"


@tool("create_medication_schedule", description="Create a reminder schedule for one of my medications.")
def create_medication_schedule(
    runtime: ToolRuntime[Context],
    medication_id: int,
    reminder_times: List[str],
    frequency: str = "daily",
    advance_minutes: int = 15
) -> str:
    """
    Create a reminder schedule for a medication.

    Args:
        medication_id: The ID of the patient medication
        reminder_times: List of times in HH:MM format (e.g., ["08:00", "20:00"])
        frequency: How often to repeat ('daily', 'twice_daily', 'three_times_daily')
        advance_minutes: Send reminder X minutes before scheduled time

    Returns:
        Confirmation of schedule creation
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Verify the medication belongs to the user and is active
        patient_med = db.query(PatientMedication).filter(
            PatientMedication.id == medication_id,
            PatientMedication.patient_id == user_id,
            PatientMedication.status == "active"
        ).first()

        if not patient_med:
            return "Medication not found, doesn't belong to you, or is not active."

        # Check if schedule already exists
        existing_schedule = db.query(ReminderSchedule).filter(
            ReminderSchedule.patient_medication_id == medication_id
        ).first()

        if existing_schedule:
            return f"A reminder schedule already exists for this medication. Use 'update_medication_schedule' to modify it."

        # Validate frequency
        try:
            freq_enum = ReminderFrequencyEnum[frequency]
        except KeyError:
            return f"Invalid frequency '{frequency}'. Valid options: daily, twice_daily, three_times_daily, custom"

        # Validate times format
        validated_times = []
        for time_str in reminder_times:
            try:
                datetime.strptime(time_str, "%H:%M")
                validated_times.append(time_str)
            except ValueError:
                return f"Invalid time format '{time_str}'. Please use HH:MM format (e.g., '08:00')."

        # Create the schedule
        schedule = ReminderSchedule(
            patient_medication_id=medication_id,
            patient_id=user_id,
            is_active=True,
            frequency=freq_enum,
            reminder_times=validated_times,
            advance_minutes=advance_minutes,
            start_date=datetime.now()
        )

        db.add(schedule)
        db.commit()

        med_name = patient_med.medication.name if patient_med.medication else "Unknown medication"
        response = f"Successfully created reminder schedule for {med_name}.\n"
        response += f"Reminders will be sent at: {', '.join(validated_times)}\n"
        response += f"Frequency: {frequency.replace('_', ' ')}\n"
        response += f"Advance notice: {advance_minutes} minutes before"

        logger.info(f"Medication schedule created for user {user_id}: medication_id {medication_id}, times {validated_times}")
        return response

    except Exception as e:
        logger.error(f"Error creating medication schedule for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error creating medication schedule: {str(e)}"
    finally:
        db.close()


@tool("update_medication_schedule", description="Update an existing medication reminder schedule.")
def update_medication_schedule(
    runtime: ToolRuntime[Context],
    medication_id: int,
    reminder_times: Optional[List[str]] = None,
    frequency: Optional[str] = None,
    advance_minutes: Optional[int] = None,
    is_active: Optional[bool] = None
) -> str:
    """
    Update an existing medication reminder schedule.

    Args:
        medication_id: The ID of the patient medication
        reminder_times: New list of times in HH:MM format (optional)
        frequency: New frequency (optional)
        advance_minutes: New advance notice minutes (optional)
        is_active: Whether to activate/deactivate the schedule (optional)

    Returns:
        Confirmation of schedule update
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Find the existing schedule
        schedule = db.query(ReminderSchedule).join(PatientMedication).filter(
            ReminderSchedule.patient_medication_id == medication_id,
            PatientMedication.patient_id == user_id
        ).first()

        if not schedule:
            return "No reminder schedule found for this medication. Use 'create_medication_schedule' to create one."

        # Validate and update frequency if provided
        if frequency:
            try:
                freq_enum = ReminderFrequencyEnum[frequency]
                schedule.frequency = freq_enum
            except KeyError:
                return f"Invalid frequency '{frequency}'. Valid options: daily, twice_daily, three_times_daily, custom"

        # Validate and update times if provided
        if reminder_times:
            validated_times = []
            for time_str in reminder_times:
                try:
                    datetime.strptime(time_str, "%H:%M")
                    validated_times.append(time_str)
                except ValueError:
                    return f"Invalid time format '{time_str}'. Please use HH:MM format (e.g., '08:00')."
            schedule.reminder_times = validated_times

        # Update other fields if provided
        if advance_minutes is not None:
            schedule.advance_minutes = advance_minutes

        if is_active is not None:
            schedule.is_active = is_active

        db.commit()

        med_name = schedule.patient_medication.medication.name if schedule.patient_medication and schedule.patient_medication.medication else "Unknown medication"

        response = f"Successfully updated reminder schedule for {med_name}.\n"
        if reminder_times:
            response += f"New reminder times: {', '.join(reminder_times)}\n"
        if frequency:
            response += f"New frequency: {frequency.replace('_', ' ')}\n"
        if advance_minutes is not None:
            response += f"New advance notice: {advance_minutes} minutes\n"
        if is_active is not None:
            status = "activated" if is_active else "deactivated"
            response += f"Schedule {status}"

        logger.info(f"Medication schedule updated for user {user_id}: medication_id {medication_id}")
        return response

    except Exception as e:
        logger.error(f"Error updating medication schedule for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error updating medication schedule: {str(e)}"
    finally:
        db.close()


@tool("delete_medication_schedule", description="Delete a medication reminder schedule.")
def delete_medication_schedule(
    runtime: ToolRuntime[Context],
    medication_id: int
) -> str:
    """
    Delete a medication reminder schedule.

    Args:
        medication_id: The ID of the patient medication

    Returns:
        Confirmation of schedule deletion
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Find the existing schedule
        schedule = db.query(ReminderSchedule).join(PatientMedication).filter(
            ReminderSchedule.patient_medication_id == medication_id,
            PatientMedication.patient_id == user_id
        ).first()

        if not schedule:
            return "No reminder schedule found for this medication."

        med_name = schedule.patient_medication.medication.name if schedule.patient_medication and schedule.patient_medication.medication else "Unknown medication"

        db.delete(schedule)
        db.commit()

        response = f"Successfully deleted reminder schedule for {med_name}."

        logger.info(f"Medication schedule deleted for user {user_id}: medication_id {medication_id}")
        return response

    except Exception as e:
        logger.error(f"Error deleting medication schedule for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error deleting medication schedule: {str(e)}"
    finally:
        db.close()