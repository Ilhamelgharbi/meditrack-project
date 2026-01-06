from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum

class RoleEnum(str, enum.Enum):
    patient = "patient"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.patient, nullable=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient_profile = relationship("Patient", foreign_keys="Patient.user_id", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assigned_patients = relationship("Patient", foreign_keys="Patient.assigned_admin_id", back_populates="assigned_admin")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
