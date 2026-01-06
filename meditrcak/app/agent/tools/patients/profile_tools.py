# app/agent/tools/patients/profile_tools.py
"""
Patient Tools for Profile Management - Direct Database Access Version

Uses direct database access through PatientService instead of HTTP calls.
This avoids the self-calling timeout issue when agent tools make HTTP requests.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
import logging
import json

from app.database.db import get_db
from app.patients.services import PatientService
from app.patients.schemas import PatientResponse, UserBasicInfo
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Context(TypedDict):
    """Context passed to tools from the agent runtime."""
    user_id: str
    token: str
    role: str


# ============================================================================
# PATIENT PROFILE TOOLS - DIRECT DATABASE ACCESS
# ============================================================================

@tool("get_my_profile", description="Get my complete patient profile information including personal details, medical history, and vitals.")
def get_my_profile(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get comprehensive information about my patient profile.
    DIRECT DATABASE ACCESS VERSION: Uses PatientService instead of HTTP calls.

    Returns:
        Complete patient profile including personal info, vitals, and medical history
    """
    try:
        # Get context from runtime.config instead of runtime.context
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get patient data directly from database using service
            patient = PatientService.get_patient_by_user_id(db, user_id)

            # Format response as structured text for agent consumption
            response_lines = []

            # User information
            if patient.user:
                response_lines.append(f"Name: {patient.user.full_name}")
                response_lines.append(f"Email: {patient.user.email}")
                response_lines.append(f"Phone: {patient.user.phone or 'Not provided'}")
                response_lines.append(f"Role: {patient.user.role.value}")

            # Personal information
            response_lines.append(f"Date of Birth: {patient.date_of_birth.isoformat() if patient.date_of_birth else 'Not provided'}")
            response_lines.append(f"Gender: {patient.gender.value if patient.gender else 'Not provided'}")

            # Medical information
            response_lines.append(f"Blood Type: {patient.blood_type or 'Not provided'}")
            response_lines.append(f"Height: {patient.height} cm" if patient.height else "Height: Not provided")
            response_lines.append(f"Weight: {patient.weight} kg" if patient.weight else "Weight: Not provided")

            # Health status
            response_lines.append(f"Status: {patient.status.value}")
            response_lines.append(f"Medical History: {patient.medical_history or 'Not provided'}")
            response_lines.append(f"Allergies: {patient.allergies or 'None reported'}")

            # Timestamps
            response_lines.append(f"Profile Created: {patient.created_at.isoformat() if patient.created_at else 'Unknown'}")
            response_lines.append(f"Last Updated: {patient.updated_at.isoformat() if patient.updated_at else 'Never'}")

            response = "\n".join(response_lines)
            logger.info(f"Profile data retrieved for user {user_id}: {len(response)} chars")
            return response

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error getting profile for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving profile: {str(e)}"


@tool("get_my_vitals", description="Get my current vital signs and measurements.")
def get_my_vitals(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get current vital signs and measurements.
    DIRECT DATABASE ACCESS VERSION: Uses PatientService instead of HTTP calls.

    Returns:
        Current vitals including height, weight, and blood type
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get patient data directly from database using service
            patient = PatientService.get_patient_by_user_id(db, user_id)

            vitals_data = {
                "height": patient.height,
                "weight": patient.weight,
                "blood_type": patient.blood_type,
                "bmi": round(patient.weight / ((patient.height/100) ** 2), 1) if patient.height and patient.weight else None
            }

            # Format as structured text for agent consumption
            response_lines = []
            response_lines.append(f"Height: {vitals_data['height']} cm" if vitals_data['height'] else "Height: Not provided")
            response_lines.append(f"Weight: {vitals_data['weight']} kg" if vitals_data['weight'] else "Weight: Not provided")
            if vitals_data['bmi']:
                response_lines.append(f"BMI: {vitals_data['bmi']}")
            response_lines.append(f"Blood Type: {vitals_data['blood_type'] or 'Not provided'}")

            response = "\n".join(response_lines)
            logger.info(f"Vitals data retrieved for user {user_id}")
            return response

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error getting vitals for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving vitals: {str(e)}"


@tool("update_my_profile", description="Update any of my personal profile information including contact details, medical history, or allergies. Use this when the user wants to change their profile data like phone number, email, medical conditions, or allergies.")
def update_my_profile(
    runtime: ToolRuntime[Context],
    email: Optional[str] = None,
    phone: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    gender: Optional[str] = None,
    blood_type: Optional[str] = None,
    height: Optional[float] = None,
    weight: Optional[float] = None,
    medical_history: Optional[str] = None,
    allergies: Optional[str] = None
) -> str:
    """
    Update my patient profile information.
    DIRECT DATABASE ACCESS VERSION: Uses PatientService instead of HTTP calls.

    Args:
        email: New email address
        phone: New phone number
        date_of_birth: Date of birth (YYYY-MM-DD format)
        gender: Gender (male/female/other)
        blood_type: Blood type
        height: Height in cm
        weight: Weight in kg
        medical_history: Medical history text
        allergies: Allergies text

    Returns:
        Confirmation of successful update
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get current patient data
            patient = PatientService.get_patient_by_user_id(db, user_id)

            # Prepare update data
            from app.patients.schemas import PatientUpdate
            from datetime import datetime

            update_data = {}

            # User fields
            if email is not None:
                update_data['email'] = email
            if phone is not None:
                update_data['phone'] = phone

            # Patient fields
            if date_of_birth is not None:
                try:
                    update_data['date_of_birth'] = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except ValueError:
                    return "Error: Invalid date format. Use YYYY-MM-DD format."

            if gender is not None:
                from app.patients.models import GenderEnum
                try:
                    update_data['gender'] = GenderEnum(gender.lower())
                except ValueError:
                    return f"Error: Invalid gender. Must be one of: {[e.value for e in GenderEnum]}"

            if blood_type is not None:
                update_data['blood_type'] = blood_type
            if height is not None:
                update_data['height'] = height
            if weight is not None:
                update_data['weight'] = weight
            if medical_history is not None:
                update_data['medical_history'] = medical_history
            if allergies is not None:
                update_data['allergies'] = allergies

            # Create update schema and apply
            patient_update = PatientUpdate(**update_data)
            updated_patient = PatientService.update_patient(db, patient.id, patient_update)

            logger.info(f"Profile updated for user {user_id}")
            return "✅ Profile updated successfully!"

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error updating profile for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error updating profile: {str(e)}"


@tool("update_my_vitals", description="Update my vital signs and measurements including height, weight, and blood type. Use this when the user wants to change their physical measurements or blood type information.")
def update_my_vitals(
    runtime: ToolRuntime[Context],
    height: Optional[float] = None,
    weight: Optional[float] = None,
    blood_type: Optional[str] = None
) -> str:
    """
    Update my vital signs and measurements.
    DIRECT DATABASE ACCESS VERSION: Uses PatientService instead of HTTP calls.

    Args:
        height: Height in cm
        weight: Weight in kg
        blood_type: Blood type

    Returns:
        Confirmation of successful update
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        try:
            # Get current patient data
            patient = PatientService.get_patient_by_user_id(db, user_id)

            # Prepare update data
            from app.patients.schemas import PatientUpdate

            update_data = {}
            if height is not None:
                update_data['height'] = height
            if weight is not None:
                update_data['weight'] = weight
            if blood_type is not None:
                update_data['blood_type'] = blood_type

            # Create update schema and apply
            patient_update = PatientUpdate(**update_data)
            updated_patient = PatientService.update_patient(db, patient.id, patient_update)

            logger.info(f"Vitals updated for user {user_id}")
            return "✅ Vitals updated successfully!"

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error updating vitals for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error updating vitals: {str(e)}"