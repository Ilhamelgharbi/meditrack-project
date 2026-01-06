# app/agent/tools/patients/logging_tools.py
"""
Patient Tools for Medication Logging and Actions.

Allows patients to log medication actions like taken, skipped, etc.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.database.db import get_db
from app.adherence.models import MedicationLog, MedicationLogStatusEnum
from app.medications.models import PatientMedication, Medication
from sqlalchemy import func

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
# PATIENT MEDICATION LOGGING TOOLS
# ============================================================================

@tool("log_medication_taken", description="Log that I took a medication dose by name.")
def log_medication_taken(
    runtime: ToolRuntime[Context],
    medication_name: str,
    notes: Optional[str] = None
) -> str:
    """
    Log that I took a medication dose.

    Args:
        medication_name: The name of the medication (e.g., "Amlodipine", "Metformin")
        notes: Optional notes about taking the medication

    Returns:
        Confirmation of logged action
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Find the patient medication by name
        patient_med = db.query(PatientMedication).join(PatientMedication.medication).filter(
            PatientMedication.patient_id == user_id,
            PatientMedication.status == "active",
            func.lower(Medication.name).like(f"%{medication_name.lower()}%")
        ).first()

        if not patient_med:
            return f"Medication '{medication_name}' not found in your active medications. Please check the spelling or use 'get_my_medications' to see your current medications."

        medication_id = patient_med.id

        # Create medication log entry
        log_entry = MedicationLog(
            patient_medication_id=medication_id,
            patient_id=user_id,
            scheduled_time=datetime.now(),  # Use current time as scheduled time for manual logging
            scheduled_date=datetime.now().date(),
            status=MedicationLogStatusEnum.taken,
            actual_time=datetime.now(),
            on_time=True,  # Assume on time for manual logging
            notes=notes,
            logged_via="agent"
        )

        db.add(log_entry)
        db.commit()

        med_name = patient_med.medication.name if patient_med.medication else "Unknown medication"
        response = f"Successfully logged that you took {med_name} ({patient_med.dosage})."

        if notes:
            response += f" Notes: {notes}"

        logger.info(f"Medication taken logged for user {user_id}: medication_id {medication_id}")
        return response

    except Exception as e:
        logger.error(f"Error logging medication taken for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error logging medication action: {str(e)}"
    finally:
        db.close()


@tool("log_medication_skipped", description="Log that I skipped a medication dose by name.")
def log_medication_skipped(
    runtime: ToolRuntime[Context],
    medication_name: str,
    reason: Optional[str] = None
) -> str:
    """
    Log that I skipped a medication dose.

    Args:
        medication_name: The name of the medication (e.g., "Amlodipine", "Metformin")
        reason: Optional reason for skipping

    Returns:
        Confirmation of logged action
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Find the patient medication by name
        patient_med = db.query(PatientMedication).join(PatientMedication.medication).filter(
            PatientMedication.patient_id == user_id,
            PatientMedication.status == "active",
            func.lower(Medication.name).like(f"%{medication_name.lower()}%")
        ).first()

        if not patient_med:
            return f"Medication '{medication_name}' not found in your active medications. Please check the spelling or use 'get_my_medications' to see your current medications."

        medication_id = patient_med.id

        # Create medication log entry
        log_entry = MedicationLog(
            patient_medication_id=medication_id,
            patient_id=user_id,
            scheduled_time=datetime.now(),
            scheduled_date=datetime.now().date(),
            status=MedicationLogStatusEnum.skipped,
            skipped_reason=reason,
            logged_via="agent"
        )

        db.add(log_entry)
        db.commit()

        med_name = patient_med.medication.name if patient_med.medication else "Unknown medication"
        response = f"Successfully logged that you skipped {med_name} ({patient_med.dosage})."

        if reason:
            response += f" Reason: {reason}"

        logger.info(f"Medication skipped logged for user {user_id}: medication_id {medication_id}")
        return response

    except Exception as e:
        logger.error(f"Error logging medication skipped for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error logging medication action: {str(e)}"
    finally:
        db.close()


@tool("get_recent_medication_logs", description="Get my recent medication logging history.")
def get_recent_medication_logs(
    runtime: ToolRuntime[Context],
    days: int = 7
) -> str:
    """
    Get my recent medication logging history.

    Args:
        days: Number of days to look back (default 7)

    Returns:
        List of recent medication log entries
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        from datetime import timedelta
        start_date = datetime.now().date() - timedelta(days=days)

        logs = db.query(MedicationLog).filter(
            MedicationLog.patient_id == user_id,
            MedicationLog.scheduled_date >= start_date
        ).order_by(MedicationLog.scheduled_date.desc(), MedicationLog.scheduled_time.desc()).limit(20).all()

        if not logs:
            return f"No medication logs found in the last {days} days."

        response_lines = [f"Your medication logs for the last {days} days:"]
        for log in logs:
            date_str = log.scheduled_date.strftime("%Y-%m-%d")
            time_str = log.scheduled_time.strftime("%I:%M %p") if log.scheduled_time else "N/A"
            status_str = log.status.value

            # Get medication name
            med_name = "Unknown"
            if log.patient_medication and log.patient_medication.medication:
                med_name = log.patient_medication.medication.name

            response_lines.append(f"• {date_str} {time_str} - {med_name} - {status_str}")

        response = "\n".join(response_lines)
        logger.info(f"Recent medication logs retrieved for user {user_id}: {len(logs)} entries")
        return response

    except Exception as e:
        logger.error(f"Error getting recent medication logs for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving medication logs: {str(e)}"
    finally:
        db.close()