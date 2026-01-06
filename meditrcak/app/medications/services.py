from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.medications.models import Medication, PatientMedication, InactiveMedication, MedicationStatusEnum
from app.medications.schemas import (
    MedicationCreate, MedicationUpdate,
    PatientMedicationCreate, PatientMedicationUpdate,
    PatientMedicationStop
)
from app.auth.models import User, RoleEnum


class MedicationService:
    """Service for managing medications in the catalog"""
    
    @staticmethod
    def create_medication(db: Session, medication_data: MedicationCreate, doctor_id: int) -> Medication:
        """Create a new medication in the catalog (admin only)"""
        # Check if medication with same name and form already exists
        existing = db.query(Medication).filter(
            Medication.name == medication_data.name,
            Medication.form == medication_data.form
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medication '{medication_data.name}' with form '{medication_data.form}' already exists"
            )
        
        new_medication = Medication(
            name=medication_data.name,
            form=medication_data.form,
            default_dosage=medication_data.default_dosage,
            side_effects=medication_data.side_effects,
            warnings=medication_data.warnings,
            created_by=doctor_id
        )
        
        db.add(new_medication)
        db.commit()
        db.refresh(new_medication)
        
        return new_medication
    
    @staticmethod
    def get_all_medications(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Medication]:
        """Get all medications with optional search"""
        query = db.query(Medication)
        
        if search:
            query = query.filter(Medication.name.ilike(f"%{search}%"))
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_medication_by_id(db: Session, medication_id: int) -> Medication:
        """Get medication by ID"""
        medication = db.query(Medication).filter(Medication.id == medication_id).first()
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        return medication
    
    @staticmethod
    def update_medication(
        db: Session,
        medication_id: int,
        medication_data: MedicationUpdate
    ) -> Medication:
        """Update medication details (admin only)"""
        medication = MedicationService.get_medication_by_id(db, medication_id)
        
        update_data = medication_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(medication, field, value)
        
        db.commit()
        db.refresh(medication)
        
        return medication
    
    @staticmethod
    def delete_medication(db: Session, medication_id: int) -> None:
        """Delete medication (admin only) - only if not assigned to any patient"""
        medication = MedicationService.get_medication_by_id(db, medication_id)
        
        # Check if medication is assigned to any patient
        active_assignments = db.query(PatientMedication).filter(
            PatientMedication.medication_id == medication_id
        ).first()
        
        if active_assignments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete medication that is assigned to patients"
            )
        
        db.delete(medication)
        db.commit()


class PatientMedicationService:
    """Service for managing patient medication assignments"""
    
    @staticmethod
    def assign_medication_to_patient(
        db: Session,
        patient_id: int,
        medication_data: PatientMedicationCreate,
        doctor_id: int
    ) -> PatientMedication:
        """Assign medication to patient (admin only) - creates with pending status or reactivates stopped medication"""
        # Verify patient exists
        patient = db.query(User).filter(
            User.id == patient_id,
            User.role == RoleEnum.patient
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Verify medication exists
        medication = MedicationService.get_medication_by_id(db, medication_data.medication_id)
        
        # Check for existing non-stopped assignments
        active_assignments = db.query(PatientMedication).filter(
            PatientMedication.patient_id == patient_id,
            PatientMedication.medication_id == medication_data.medication_id,
            PatientMedication.status != MedicationStatusEnum.stopped
        ).all()
        
        # Check for stopped assignments to reactivate
        stopped_assignment = db.query(PatientMedication).filter(
            PatientMedication.patient_id == patient_id,
            PatientMedication.medication_id == medication_data.medication_id,
            PatientMedication.status == MedicationStatusEnum.stopped
        ).order_by(PatientMedication.updated_at.desc()).first()
        
        if stopped_assignment and not active_assignments:
            # Only allow reactivation if there are no active assignments
            # Delete any other stopped assignments for this medication to prevent duplicates
            other_stopped = db.query(PatientMedication).filter(
                PatientMedication.patient_id == patient_id,
                PatientMedication.medication_id == medication_data.medication_id,
                PatientMedication.status == MedicationStatusEnum.stopped,
                PatientMedication.id != stopped_assignment.id
            ).all()
            
            for other in other_stopped:
                db.delete(other)
            
            # Reactivate the most recent stopped medication
            stopped_assignment.status = MedicationStatusEnum.pending
            stopped_assignment.confirmed_by_patient = False
            stopped_assignment.assigned_by_doctor = doctor_id
            
            # Update medication details
            stopped_assignment.dosage = medication_data.dosage
            stopped_assignment.instructions = medication_data.instructions
            stopped_assignment.times_per_day = medication_data.times_per_day
            stopped_assignment.start_date = medication_data.start_date
            stopped_assignment.end_date = medication_data.end_date
            
            db.commit()
            db.refresh(stopped_assignment)
            return stopped_assignment
        elif active_assignments:
            # No stopped medication to reactivate, but already have active assignments
            # Clean up duplicates - keep only the most recent active/pending assignment
            if len(active_assignments) > 1:
                # Sort by updated_at desc, keep the first (most recent), delete others
                active_assignments.sort(key=lambda x: x.updated_at, reverse=True)
                for old_assignment in active_assignments[1:]:
                    db.delete(old_assignment)
                db.commit()
                # Refresh the kept assignment
                db.refresh(active_assignments[0])
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient already has this medication assigned (status: {active_assignments[0].status})"
            )
        
        # Validate dates
        if medication_data.end_date and medication_data.end_date < medication_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be before start date"
            )
        
        # Create new patient medication assignment
        patient_medication = PatientMedication(
            patient_id=patient_id,
            medication_id=medication_data.medication_id,
            dosage=medication_data.dosage,
            instructions=medication_data.instructions,
            times_per_day=medication_data.times_per_day,
            start_date=medication_data.start_date,
            end_date=medication_data.end_date,
            status=MedicationStatusEnum.pending,
            confirmed_by_patient=False,
            assigned_by_doctor=doctor_id
        )
        
        db.add(patient_medication)
        db.commit()
        db.refresh(patient_medication)
        
        return patient_medication
    
    @staticmethod
    def get_patient_medications(
        db: Session,
        patient_id: int,
        status_filter: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[PatientMedication]:
        """Get all medications for a patient with medication details"""
        query = db.query(PatientMedication).join(
            Medication, PatientMedication.medication_id == Medication.id
        ).filter(PatientMedication.patient_id == patient_id)
        
        if not include_inactive:
            query = query.filter(PatientMedication.status != MedicationStatusEnum.stopped)
        
        if status_filter:
            query = query.filter(PatientMedication.status == status_filter)
        
        return query.all()
    
    @staticmethod
    def get_patient_medication_by_id(
        db: Session,
        patient_medication_id: int
    ) -> PatientMedication:
        """Get specific patient medication assignment"""
        patient_medication = db.query(PatientMedication).filter(
            PatientMedication.id == patient_medication_id
        ).first()
        
        if not patient_medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient medication assignment not found"
            )
        
        return patient_medication
    
    @staticmethod
    def confirm_medication(
        db: Session,
        patient_medication_id: int,
        patient_id: int
    ) -> PatientMedication:
        """Patient confirms to start taking medication - changes status from pending to active"""
        patient_medication = PatientMedicationService.get_patient_medication_by_id(
            db, patient_medication_id
        )
        
        # Verify this medication belongs to the patient
        if patient_medication.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only confirm your own medications"
            )
        
        # Verify medication is in pending status
        if patient_medication.status != MedicationStatusEnum.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medication is already {patient_medication.status}"
            )
        
        # Update status to active
        patient_medication.status = MedicationStatusEnum.active
        patient_medication.confirmed_by_patient = True
        
        db.commit()
        db.refresh(patient_medication)
        
        return patient_medication
    
    @staticmethod
    def update_patient_medication(
        db: Session,
        patient_medication_id: int,
        medication_data: PatientMedicationUpdate
    ) -> PatientMedication:
        """Update patient medication details (admin only)"""
        patient_medication = PatientMedicationService.get_patient_medication_by_id(
            db, patient_medication_id
        )
        
        update_data = medication_data.model_dump(exclude_unset=True)
        
        # Validate dates if both are present
        if 'end_date' in update_data and 'start_date' in update_data:
            if update_data['end_date'] and update_data['end_date'] < update_data['start_date']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End date cannot be before start date"
                )
        
        for field, value in update_data.items():
            setattr(patient_medication, field, value)
        
        db.commit()
        db.refresh(patient_medication)
        
        return patient_medication
    
    @staticmethod
    def stop_medication(
        db: Session,
        patient_medication_id: int,
        doctor_id: int,
        stop_data: PatientMedicationStop
    ) -> InactiveMedication:
        """Stop a patient's medication (admin only) - changes status to stopped and creates inactive record"""
        patient_medication = PatientMedicationService.get_patient_medication_by_id(
            db, patient_medication_id
        )
        
        # Verify medication is not already stopped
        if patient_medication.status == MedicationStatusEnum.stopped:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication is already stopped"
            )
        
        # Update patient medication status
        patient_medication.status = MedicationStatusEnum.stopped
        
        # Create inactive medication record
        inactive_medication = InactiveMedication(
            patient_medication_id=patient_medication_id,
            stopped_by=doctor_id,
            reason=stop_data.reason
        )
        
        db.add(inactive_medication)
        db.commit()
        db.refresh(inactive_medication)
        
        return inactive_medication
    
    @staticmethod
    def get_inactive_medications(
        db: Session,
        patient_id: int
    ) -> List[InactiveMedication]:
        """Get all stopped medications for a patient"""
        return db.query(InactiveMedication).join(
            PatientMedication
        ).filter(
            PatientMedication.patient_id == patient_id
        ).all()
