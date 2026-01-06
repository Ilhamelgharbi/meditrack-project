# app/agent/tools/patients/medical_tools.py
"""
Patient Tools for Medical History and Health Information.

Provides access to patient's medical history, allergies, and other health data.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.database.db import get_db
from app.patients.models import Patient

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
# PATIENT MEDICAL HISTORY TOOLS
# ============================================================================

@tool("get_my_medical_history", description="Get my medical history and health background.")
def get_my_medical_history(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my medical history and health background information.

    Returns:
        Patient's medical history, conditions, and health background
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        patient = db.query(Patient).filter(Patient.user_id == user_id).first()
        if not patient:
            return "No patient profile found. Please complete your patient registration."

        if not patient.medical_history:
            return "No medical history information is currently recorded in your profile."

        response = f"Medical History: {patient.medical_history}"

        # Add additional context if available
        if patient.status:
            response += f"\n\nCurrent health status: {patient.status.value}"

        logger.info(f"Medical history retrieved for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error getting medical history for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving medical history: {str(e)}"
    finally:
        db.close()


@tool("get_my_allergies", description="Get my allergy information and known sensitivities.")
def get_my_allergies(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my allergy information and known sensitivities.

    Returns:
        List of patient's allergies and sensitivities
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        patient = db.query(Patient).filter(Patient.user_id == user_id).first()
        if not patient:
            return "No patient profile found. Please complete your patient registration."

        if not patient.allergies:
            return "No allergy information is currently recorded in your profile."

        response = f"Allergies: {patient.allergies}"

        logger.info(f"Allergies retrieved for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error getting allergies for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving allergy information: {str(e)}"
    finally:
        db.close()


@tool("get_my_health_summary", description="Get a summary of my current health status and key information.")
def get_my_health_summary(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get a comprehensive summary of my current health status and key information.

    Returns:
        Summary of patient's health status, vitals, medications, and other key info
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        patient = db.query(Patient).filter(Patient.user_id == user_id).first()
        if not patient:
            return "No patient profile found. Please complete your patient registration."

        # Build health summary
        summary_lines = ["Your Health Summary:"]

        # Basic info
        if patient.date_of_birth:
            from datetime import datetime
            age = datetime.now().year - patient.date_of_birth.year
            summary_lines.append(f"• Age: {age} years old")

        if patient.gender:
            summary_lines.append(f"• Gender: {patient.gender.value}")

        if patient.blood_type:
            summary_lines.append(f"• Blood Type: {patient.blood_type}")

        # Health status
        if patient.status:
            summary_lines.append(f"• Health Status: {patient.status.value}")

        # Physical measurements
        vitals = []
        if patient.height:
            vitals.append(f"Height: {patient.height}cm")
        if patient.weight:
            vitals.append(f"Weight: {patient.weight}kg")
        if vitals:
            summary_lines.append(f"• Vitals: {', '.join(vitals)}")

        # Medical info
        if patient.medical_history:
            summary_lines.append(f"• Medical History: {patient.medical_history[:100]}{'...' if len(patient.medical_history) > 100 else ''}")

        if patient.allergies:
            summary_lines.append(f"• Allergies: {patient.allergies}")

        if patient.current_medications:
            summary_lines.append(f"• Current Medications: {patient.current_medications}")

        if len(summary_lines) == 1:
            return "Your health profile is not yet complete. Please update your patient information."

        response = "\n".join(summary_lines)
        logger.info(f"Health summary retrieved for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error getting health summary for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving health summary: {str(e)}"
    finally:
        db.close()