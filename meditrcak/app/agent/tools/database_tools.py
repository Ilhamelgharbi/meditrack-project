# app/ai/tools/database_tools.py
import json
import os
from pathlib import Path
from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.patients.models import Patient
from app.auth.models import User
from app.medications.models import Medication, PatientMedication

class Context(TypedDict):
    user_id: str

# Removed JSON database loading - now using SQLAlchemy

@tool("get_patient_info",description="Fetch the patient's medical profile including conditions, allergies, vitals, and history.")
def get_patient_info(runtime: ToolRuntime[Context]) -> Dict[str, Any]:
    """Get comprehensive patient medical profile and history from the database."""
    user_id = runtime.context["user_id"]
    db: Session = next(get_db())
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if patient:
            user = db.query(User).filter(User.id == patient.user_id).first()
            name = user.full_name if user else f"User {user_id}"
            return {
                "name": name,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender.value if patient.gender else None,
                "status": patient.status.value if patient.status else None,
                "medical_history": patient.medical_history,
                "allergies": patient.allergies,
                "current_medications": patient.current_medications
            }
        else:
            return {"error": "Patient not found."}
    finally:
        db.close()

@tool("get_user_name", description="Get the patient's name from the database.")
def get_user_name(runtime: ToolRuntime[Context]) -> Dict[str, Any]:
    user_id = runtime.context["user_id"]
    db: Session = next(get_db())
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if patient:
            user = db.query(User).filter(User.id == patient.user_id).first()
            name = user.full_name if user else f"User {user_id}"
            return {"name": name}
        else:
            return {"error": "Unknown"}
    finally:
        db.close()


@tool("get_user_medications", description="Retrieve the active medications for the current patient, including medication name, dosage, and usage instructions. Use this tool when the user asks about their medications, pills, treatments, or what they are currently taking.")
def get_user_medications(runtime: ToolRuntime[Context]) -> Dict[str, Any]:
    user_id = runtime.context["user_id"]
    db: Session = next(get_db())
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return {"error": "Patient not found."}
        
        # Get active patient medications
        patient_meds = db.query(PatientMedication).filter(
            PatientMedication.patient_id == int(user_id),
            PatientMedication.status == 'active'
        ).all()
        
        if not patient_meds:
            return {"medications": []}
        
        result = []
        for pm in patient_meds:
            medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
            if medication:
                result.append({
                    "name": medication.name,
                    "dosage": pm.dosage,
                    "instructions": pm.instructions
                })
        return {"medications": result}
    finally:
        db.close()