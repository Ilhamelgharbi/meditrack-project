# app/agent/tools/patients/medication_tools.py
"""
Patient Tools for Medication Management - Direct Database Access Version

Uses direct database access through PatientMedicationService instead of HTTP calls.
This avoids the self-calling timeout issue when agent tools make HTTP requests.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
import logging
import json

from app.database.db import get_db
from app.medications.services import PatientMedicationService
from app.medications.models import MedicationStatusEnum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Context(TypedDict):
    """Context passed to tools from the agent runtime."""
    user_id: str
    token: str
    role: str


# ============================================================================
# PATIENT MEDICATION TOOLS - DIRECT DATABASE ACCESS
# ============================================================================

@tool("get_my_medications", description="Get all my medications with optional status filtering.")
def get_my_medications(
    runtime: ToolRuntime[Context],
    status_filter: Optional[str] = None,
    include_inactive: bool = False
) -> str:
    """
    Get my medications with optional filtering.
    DIRECT DATABASE ACCESS VERSION: Uses PatientMedicationService instead of HTTP calls.

    Args:
        status_filter: Filter by status ('pending', 'active', 'stopped')
        include_inactive: Whether to include stopped medications

    Returns:
        List of my medications with details
    """
    try:
        # Get context from runtime.config instead of runtime.context
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get patient medications directly from database using service
            patient_medications = PatientMedicationService.get_patient_medications(
                db, user_id, status_filter, include_inactive
            )

            if not patient_medications:
                # Return specific message based on status filter
                if status_filter == "active":
                    return "You have no active medications."
                elif status_filter == "pending":
                    return "You have no pending medications."
                elif status_filter == "stopped":
                    return "You have no stopped medications."
                else:
                    return "You have no medications assigned."

            # Format response as structured text for agent consumption
            response_lines = []
            active_count = 0
            pending_count = 0

            for pm in patient_medications:
                if pm.status == MedicationStatusEnum.active:
                    active_count += 1
                elif pm.status == MedicationStatusEnum.pending:
                    pending_count += 1

                # Format medication info in structured way
                med_name = pm.medication.name
                form = pm.medication.form.value if pm.medication.form else "Form not specified"
                dosage = pm.dosage or "Dosage not specified"
                frequency = f"{pm.times_per_day} times per day" if pm.times_per_day else "Frequency not specified"
                instructions = pm.instructions or "Instructions not provided"
                start_date = pm.start_date.strftime('%Y-%m-%d') if pm.start_date else "Start date not specified"
                side_effects = pm.medication.side_effects or "Side effects not specified"
                warnings = pm.medication.warnings or "Warnings not specified"

                response_lines.append(f"Medication: {med_name}")
                response_lines.append(f"Form: {form}")
                response_lines.append(f"Dosage: {dosage}")
                response_lines.append(f"Frequency: {frequency}")
                response_lines.append(f"Instructions: {instructions}")
                response_lines.append(f"Start Date: {start_date}")
                response_lines.append(f"Status: {pm.status.value}")
                response_lines.append(f"Side Effects: {side_effects}")
                response_lines.append(f"Warnings: {warnings}")
                response_lines.append("---")

            # Summary at top
            if active_count > 0:
                response_lines.insert(0, f"Active Medications: {active_count}")
            if pending_count > 0:
                response_lines.insert(0, f"Pending Medications: {pending_count}")

            response = "\n".join(response_lines)
            logger.info(f"Medications retrieved for user {user_id}: {len(patient_medications)} medications")
            return response

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error getting medications for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving medications: {str(e)}"


@tool("get_active_medications", description="Get only my currently active medications.")
def get_active_medications(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my currently active medications.
    DIRECT DATABASE ACCESS VERSION: Uses PatientMedicationService instead of HTTP calls.

    Returns:
        List of active medications
    """
    return get_my_medications.func(runtime, status_filter="active", include_inactive=False)


@tool("get_pending_medications", description="Get my pending medications that need confirmation.")
def get_pending_medications(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my pending medications that need to be confirmed.
    DIRECT DATABASE ACCESS VERSION: Uses PatientMedicationService instead of HTTP calls.

    Returns:
        List of pending medications
    """
    return get_my_medications.func(runtime, status_filter="pending", include_inactive=False)


@tool("confirm_medication", description="Confirm and start taking a pending medication by name.")
def confirm_medication(
    runtime: ToolRuntime[Context],
    medication_name: str
) -> str:
    """
    Confirm to start taking a pending medication.
    DIRECT DATABASE ACCESS VERSION: Uses PatientMedicationService instead of HTTP calls.

    Args:
        medication_name: The name of the medication to confirm (must be pending)

    Returns:
        Confirmation message
    """
    try:
        # Get context from runtime.config instead of runtime.context
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # First, find the pending medication with this name
            from app.medications.services import PatientMedicationService
            pending_meds = PatientMedicationService.get_patient_medications(
                db, user_id, status_filter="pending", include_inactive=False
            )
            
            # Find the one with matching name
            target_med = None
            for pm in pending_meds:
                if pm.medication.name.lower() == medication_name.lower():
                    target_med = pm
                    break
            
            if not target_med:
                return f"❌ No pending medication found with name '{medication_name}'. Please check the name and try again."
            
            # Confirm medication directly using service
            confirmed_medication = PatientMedicationService.confirm_medication(
                db, target_med.id, user_id
            )

            logger.info(f"Medication {target_med.id} ({medication_name}) confirmed for user {user_id}")
            return f"✅ Successfully confirmed {confirmed_medication.medication.name}. You can now start taking this medication."

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error confirming medication for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error confirming medication: {str(e)}"


@tool("get_inactive_medications", description="Get my previously stopped medications.")
def get_inactive_medications(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my previously stopped medications.
    DIRECT DATABASE ACCESS VERSION: Uses PatientMedicationService instead of HTTP calls.

    Returns:
        List of inactive medications
    """
    try:
        # Get context from runtime.config instead of runtime.context
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get inactive medications directly from database using service
            inactive_medications = PatientMedicationService.get_inactive_medications(db, user_id)

            if not inactive_medications:
                return "You have no previously stopped medications."

            # Format response as structured text for agent consumption
            response_lines = [f"You have {len(inactive_medications)} previously stopped medication{'s' if len(inactive_medications) != 1 else ''}:"]

            for im in inactive_medications:
                pm = im.patient_medication
                med_info = f"{pm.medication.name}: {pm.dosage or 'Dosage not specified'}"
                if pm.frequency:
                    med_info += f", {pm.frequency}"
                if im.reason:
                    med_info += f" - Stopped: {im.reason}"
                if im.stopped_at:
                    med_info += f" on {im.stopped_at.strftime('%Y-%m-%d')}"

                response_lines.append(f"• {med_info}")

            response = "\n".join(response_lines)
            logger.info(f"Inactive medications retrieved for user {user_id}: {len(inactive_medications)} medications")
            return response

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error getting inactive medications for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving inactive medications: {str(e)}"