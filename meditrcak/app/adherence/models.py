"""
Adherence tracking models
Track medication taking behavior and calculate adherence metrics
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.db import Base


class MedicationLogStatusEnum(str, enum.Enum):
    """Status of medication dose"""
    taken = "taken"
    skipped = "skipped"
    missed = "missed"  # not taken and past the time window


class MedicationLog(Base):
    """
    Log of each medication dose - taken, skipped, or missed
    Core table for adherence tracking
    """
    __tablename__ = "medication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Scheduled information
    scheduled_time = Column(DateTime, nullable=False)  # When dose was scheduled
    scheduled_date = Column(Date, nullable=False, index=True)  # Date for easy filtering
    
    # Actual information
    status = Column(SQLEnum(MedicationLogStatusEnum), nullable=False, default=MedicationLogStatusEnum.missed)
    actual_time = Column(DateTime, nullable=True)  # When dose was actually taken (if taken)
    
    # Time window tracking
    on_time = Column(Boolean, default=True)  # Taken within acceptable time window (e.g., ±30 min)
    minutes_late = Column(Integer, nullable=True)  # How many minutes late (if applicable)
    
    # Additional context
    notes = Column(Text, nullable=True)  # Patient notes (e.g., "took with breakfast")
    skipped_reason = Column(String(200), nullable=True)  # Reason for skipping
    
    # Source tracking
    logged_via = Column(String(50), default="manual")  # manual, whatsapp, sms, auto
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=True)  # Which reminder triggered this
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_medication = relationship("PatientMedication")
    patient = relationship("User", foreign_keys=[patient_id])
    reminder = relationship("Reminder", foreign_keys=[reminder_id], back_populates="logs")
    
    def __repr__(self):
        return f"<MedicationLog(id={self.id}, patient_id={self.patient_id}, status={self.status}, date={self.scheduled_date})>"


class AdherenceStats(Base):
    """
    Pre-calculated adherence statistics for performance
    Updated periodically (daily/weekly) to avoid heavy calculations
    """
    __tablename__ = "adherence_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=True)  # Null = overall stats
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, overall
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Core metrics
    total_scheduled = Column(Integer, default=0)  # Total doses scheduled
    total_taken = Column(Integer, default=0)  # Doses taken (on time or late)
    total_skipped = Column(Integer, default=0)  # Intentionally skipped
    total_missed = Column(Integer, default=0)  # Missed (forgot/didn't take)
    
    # Calculated scores (0-100)
    adherence_score = Column(Float, default=0.0)  # (taken / scheduled) * 100
    on_time_score = Column(Float, default=0.0)  # (on_time_taken / total_taken) * 100
    
    # Streak tracking
    current_streak = Column(Integer, default=0)  # Days in a row with 100% adherence
    longest_streak = Column(Integer, default=0)  # Best streak in this period
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    patient_medication = relationship("PatientMedication", foreign_keys=[patient_medication_id])
    
    def __repr__(self):
        return f"<AdherenceStats(patient_id={self.patient_id}, period={self.period_type}, score={self.adherence_score})>"


class AdherenceGoal(Base):
    """
    Patient or doctor-set adherence goals
    """
    __tablename__ = "adherence_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=True)  # Null = overall goal
    
    # Goal configuration
    target_adherence_score = Column(Float, default=80.0)  # Target percentage
    target_streak_days = Column(Integer, default=7)  # Target consecutive days
    
    # Progress tracking
    current_progress = Column(Float, default=0.0)
    is_achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime, nullable=True)
    
    # Metadata
    set_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Doctor or patient
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    patient_medication = relationship("PatientMedication", foreign_keys=[patient_medication_id])
    set_by_user = relationship("User", foreign_keys=[set_by])
    
    def __repr__(self):
        return f"<AdherenceGoal(patient_id={self.patient_id}, target={self.target_adherence_score}%, achieved={self.is_achieved})>"
