from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class StatusEnum(str, enum.Enum):
    stable = "stable"
    critical = "critical"
    under_observation = "under_observation"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal Information
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(GenderEnum), nullable=True)
    
    # Medical Information
    blood_type = Column(String(5), nullable=True)
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    
    # Health Status
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.stable, nullable=False)
    medical_history = Column(String(2000), nullable=True)
    allergies = Column(String(500), nullable=True)
    current_medications = Column(String(1000), nullable=True)
    
    # Admin Assignment (patients assigned to admin by default)
    assigned_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="patient_profile")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id], back_populates="assigned_patients")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, user_id={self.user_id}, status={self.status})>"
