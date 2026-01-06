from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.auth.services import get_current_user
from app.auth.models import User, RoleEnum
from app.medications.services import MedicationService, PatientMedicationService
from app.medications.schemas import (
    MedicationCreate, MedicationUpdate, MedicationResponse,
    PatientMedicationCreate, PatientMedicationUpdate, PatientMedicationResponse,
    PatientMedicationStop,
    InactiveMedicationResponse, PatientMedicationDetailedResponse
)

router = APIRouter(prefix="/medications", tags=["Medications"])


# ==================== MEDICATION CATALOG ROUTES ====================

@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    medication_data: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new medication in the catalog (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add medications to the catalog"
        )
    
    return MedicationService.create_medication(db, medication_data, current_user.id)


@router.get("/", response_model=List[MedicationResponse])
def get_all_medications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all medications from the catalog (Both admin and patient can access)
    """
    return MedicationService.get_all_medications(db, skip, limit, search)


@router.get("/{medication_id}", response_model=MedicationResponse)
def get_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get medication details by ID
    """
    return MedicationService.get_medication_by_id(db, medication_id)


@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: int,
    medication_data: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update medication details (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update medications"
        )
    
    return MedicationService.update_medication(db, medication_id, medication_data)


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete medication from catalog (Admin only)
    Can only delete if not assigned to any patient
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete medications"
        )
    
    MedicationService.delete_medication(db, medication_id)
    return None


# ==================== PATIENT MEDICATION ROUTES ====================

@router.post("/patients/{patient_id}/medications", response_model=PatientMedicationDetailedResponse, status_code=status.HTTP_201_CREATED)
def assign_medication_to_patient(
    patient_id: int,
    medication_data: PatientMedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign medication to a patient (Admin only)
    Creates with status='pending' until patient confirms
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign medications"
        )
    
    return PatientMedicationService.assign_medication_to_patient(
        db, patient_id, medication_data, current_user.id
    )


@router.get("/patients/{patient_id}/medications", response_model=List[PatientMedicationDetailedResponse])
def get_patient_medications(
    patient_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, active, stopped"),
    include_inactive: bool = Query(False, description="Include stopped medications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all medications for a patient
    - Admin can view any patient's medications
    - Patient can only view their own medications
    """
    # Authorization check
    if current_user.role == RoleEnum.patient and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own medications"
        )
    
    return PatientMedicationService.get_patient_medications(
        db, patient_id, status_filter, include_inactive
    )


@router.get("/patients/{patient_id}/medications/inactive", response_model=List[InactiveMedicationResponse])
def get_inactive_medications(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all stopped medications for a patient with stop details
    """
    # Authorization check
    if current_user.role == RoleEnum.patient and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own medications"
        )
    
    return PatientMedicationService.get_inactive_medications(db, patient_id)


@router.patch("/patients/{patient_id}/medications/{medication_assignment_id}/confirm", response_model=PatientMedicationDetailedResponse)
def confirm_medication(
    patient_id: int,
    medication_assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Patient confirms to start taking medication
    Changes status from 'pending' to 'active'
    """
    # Verify patient can only confirm their own medications
    if current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only confirm your own medications"
        )
    
    return PatientMedicationService.confirm_medication(
        db, medication_assignment_id, patient_id
    )


@router.put("/patients/{patient_id}/medications/{medication_assignment_id}", response_model=PatientMedicationDetailedResponse)
def update_patient_medication(
    patient_id: int,
    medication_assignment_id: int,
    medication_data: PatientMedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update patient medication details (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update patient medications"
        )
    
    return PatientMedicationService.update_patient_medication(
        db, medication_assignment_id, medication_data
    )


@router.patch("/patients/{patient_id}/medications/{medication_assignment_id}/stop", response_model=InactiveMedicationResponse)
def stop_medication(
    patient_id: int,
    medication_assignment_id: int,
    stop_data: PatientMedicationStop,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop a patient's medication (Admin only)
    Changes status to 'stopped' and creates inactive medication record
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can stop medications"
        )
    
    return PatientMedicationService.stop_medication(
        db, medication_assignment_id, current_user.id, stop_data
    )