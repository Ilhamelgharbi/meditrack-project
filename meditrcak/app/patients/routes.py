from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.auth.services import get_current_user, require_admin, require_patient
from app.auth.models import User, RoleEnum
from app.patients.schemas import PatientResponse, PatientUpdate, PatientAdminUpdate, PatientCreate
from app.patients.services import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


# Get all patients (Admin only)
@router.get("/", response_model=list[PatientResponse])
def get_all_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all patients (Admin only)"""
    patients = PatientService.get_all_patients(db, admin_id=current_user.id)
    return patients


# Get own patient profile - MUST come before /{patient_id}
@router.get("/me/profile", response_model=PatientResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """Get current user's patient profile"""
    patient = PatientService.get_patient_by_user_id(db, current_user.id)
    return patient


# Update own patient profile - MUST come before /{patient_id}
@router.put("/me/profile", response_model=PatientResponse)
def update_my_profile(
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """Update current user's patient profile"""
    patient = PatientService.get_patient_by_user_id(db, current_user.id)
    updated_patient = PatientService.update_patient(db, patient.id, patient_data)
    return updated_patient


# Get patient profile by ID (Admin only) - MUST come after /me/profile
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get patient by ID (Admin only)"""
    patient = PatientService.get_patient_by_id(db, patient_id)
    return patient


# Admin updates patient
@router.put("/{patient_id}/admin-update", response_model=PatientResponse)
def admin_update_patient(
    patient_id: int,
    admin_data: PatientAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin updates patient medical information"""
    updated_patient = PatientService.update_patient_by_admin(db, patient_id, admin_data)
    return updated_patient

