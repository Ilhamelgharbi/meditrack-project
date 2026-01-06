from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum


class MedicationFormEnum(str, enum.Enum):
    """Enum for medication forms"""
    tablet = "tablet"
    capsule = "capsule"
    syrup = "syrup"
    injection = "injection"
    cream = "cream"
    drops = "drops"
    inhaler = "inhaler"
    patch = "patch"


class MedicationStatusEnum(str, enum.Enum):
    """Enum for patient medication status"""
    pending = "pending"  # Doctor assigned, patient hasn't confirmed yet
    active = "active"    # Patient confirmed and taking medication
    stopped = "stopped"  # Doctor stopped the medication


class Medication(Base):
    """
    Master medication catalog
    Stores information about medications that can be prescribed
    """
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    form = Column(SQLEnum(MedicationFormEnum), nullable=False)
    default_dosage = Column(String(100), nullable=True)  # e.g., "500mg", "10ml"
    side_effects = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Doctor who added
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    patient_medications = relationship("PatientMedication", back_populates="medication")
    
    def __repr__(self):
        return f"<Medication(id={self.id}, name={self.name}, form={self.form})>"


class PatientMedication(Base):
    """
    Patient-specific medication assignments
    Links patients to medications with specific instructions and schedule
    """
    __tablename__ = "patient_medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    
    # Patient-specific dosage and instructions
    dosage = Column(String(100), nullable=False)  # Patient-specific dosage
    instructions = Column(Text, nullable=True)  # e.g., "Take after meals"
    times_per_day = Column(Integer, nullable=False)  # e.g., 1, 2, 3
    
    # Schedule
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Optional end date
    
    # Status and confirmation
    status = Column(SQLEnum(MedicationStatusEnum), default=MedicationStatusEnum.pending, nullable=False, index=True)
    confirmed_by_patient = Column(Boolean, default=False, nullable=False)
    
    # Assignment tracking
    assigned_by_doctor = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    medication = relationship("Medication", back_populates="patient_medications")
    assigning_doctor = relationship("User", foreign_keys=[assigned_by_doctor])
    inactive_record = relationship("InactiveMedication", back_populates="patient_medication", uselist=False)
    reminders = relationship("Reminder", back_populates="patient_medication", cascade="all, delete-orphan")
    reminder_schedule = relationship("ReminderSchedule", back_populates="patient_medication", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PatientMedication(id={self.id}, patient_id={self.patient_id}, medication_id={self.medication_id}, status={self.status})>"


class InactiveMedication(Base):
    """
    History of stopped medications
    Tracks when and why medications were discontinued
    """
    __tablename__ = "inactive_medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=False, unique=True)
    
    # Stop details
    stopped_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Doctor who stopped
    stopped_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(Text, nullable=True)
    
    # Relationships
    patient_medication = relationship("PatientMedication", back_populates="inactive_record")
    stopping_doctor = relationship("User", foreign_keys=[stopped_by])
    
    def __repr__(self):
        return f"<InactiveMedication(id={self.id}, patient_medication_id={self.patient_medication_id}, stopped_at={self.stopped_at})>"
