from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.patients.models import Patient
from app.patients.schemas import PatientCreate, PatientUpdate, PatientAdminUpdate
from app.auth.models import User, RoleEnum


class PatientService:
    
    @staticmethod
    def create_patient_profile(db: Session, user_id: int, patient_data: PatientCreate = None) -> Patient:
        """Create a patient profile for a user"""
        # Check if patient profile already exists
        existing = db.query(Patient).filter(Patient.user_id == user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient profile already exists"
            )
        
        # Find the first admin to assign to this patient
        admin = db.query(User).filter(User.role == RoleEnum.admin).first()
        
        patient = Patient(
            user_id=user_id,
            assigned_admin_id=admin.id if admin else None,
            **(patient_data.dict(exclude_unset=True) if patient_data else {})
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        return patient
    
    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int) -> Patient:
        """Get patient by ID"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        return patient
    
    @staticmethod
    def get_patient_by_user_id(db: Session, user_id: int) -> Patient:
        """Get patient by user ID"""
        patient = db.query(Patient).filter(Patient.user_id == user_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        return patient
    
    @staticmethod
    def get_all_patients(db: Session, admin_id: int = None) -> list[Patient]:
        """Get all patients, optionally filtered by admin"""
        query = db.query(Patient)
        if admin_id:
            query = query.filter(Patient.assigned_admin_id == admin_id)
        return query.all()
    
    @staticmethod
    def update_patient(db: Session, patient_id: int, patient_data: PatientUpdate) -> Patient:
        """Update patient information (by patient themselves)"""
        patient = PatientService.get_patient_by_id(db, patient_id)
        
        update_dict = patient_data.dict(exclude_unset=True)
        
        # Separate user fields from patient fields
        user_fields = ['email', 'phone']
        patient_fields = {k: v for k, v in update_dict.items() if k not in user_fields}
        user_updates = {k: v for k, v in update_dict.items() if k in user_fields}
        
        # Update patient fields
        for field, value in patient_fields.items():
            setattr(patient, field, value)
        
        # Update user fields
        if user_updates and patient.user:
            for field, value in user_updates.items():
                setattr(patient.user, field, value)
        
        db.commit()
        db.refresh(patient)
        
        return patient
    
    @staticmethod
    def update_patient_by_admin(db: Session, patient_id: int, admin_data: PatientAdminUpdate) -> Patient:
        """Update patient information (by admin)"""
        patient = PatientService.get_patient_by_id(db, patient_id)
        
        update_dict = admin_data.dict(exclude_unset=True)
        
        # Separate user fields from patient fields
        user_fields = ['email', 'phone']
        patient_fields = {k: v for k, v in update_dict.items() if k not in user_fields}
        user_updates = {k: v for k, v in update_dict.items() if k in user_fields}
        
        # Update patient fields
        for field, value in patient_fields.items():
            setattr(patient, field, value)
        
        # Update user fields
        if user_updates and patient.user:
            for field, value in user_updates.items():
                setattr(patient.user, field, value)
        
        db.commit()
        db.refresh(patient)
        
        return patient
    
    @staticmethod
    def delete_patient(db: Session, patient_id: int):
        """Delete patient profile"""
        patient = PatientService.get_patient_by_id(db, patient_id)
        db.delete(patient)
        db.commit()
