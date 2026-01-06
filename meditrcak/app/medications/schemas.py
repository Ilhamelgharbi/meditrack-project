from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


# Enums
class MedicationFormEnum(str, Enum):
    tablet = "tablet"
    capsule = "capsule"
    syrup = "syrup"
    injection = "injection"
    cream = "cream"
    drops = "drops"
    inhaler = "inhaler"
    patch = "patch"


class MedicationStatusEnum(str, Enum):
    pending = "pending"
    active = "active"
    stopped = "stopped"


# ==================== MEDICATION SCHEMAS ====================

class MedicationCreate(BaseModel):
    """Schema for creating a new medication in the catalog"""
    name: str = Field(..., min_length=1, max_length=255)
    form: MedicationFormEnum
    default_dosage: Optional[str] = Field(None, max_length=100)
    side_effects: Optional[str] = None
    warnings: Optional[str] = None


class MedicationUpdate(BaseModel):
    """Schema for updating a medication"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    form: Optional[MedicationFormEnum] = None
    default_dosage: Optional[str] = Field(None, max_length=100)
    side_effects: Optional[str] = None
    warnings: Optional[str] = None


class MedicationResponse(BaseModel):
    """Schema for medication response"""
    id: int
    name: str
    form: MedicationFormEnum
    default_dosage: Optional[str]
    side_effects: Optional[str]
    warnings: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== PATIENT MEDICATION SCHEMAS ====================

class PatientMedicationCreate(BaseModel):
    """Schema for assigning a medication to a patient"""
    medication_id: int
    dosage: str = Field(..., min_length=1, max_length=100)
    instructions: Optional[str] = None
    times_per_day: int = Field(..., ge=1, le=24)
    start_date: date
    end_date: Optional[date] = None


class PatientMedicationUpdate(BaseModel):
    """Schema for updating patient medication (doctor only)"""
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    instructions: Optional[str] = None
    times_per_day: Optional[int] = Field(None, ge=1, le=24)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PatientMedicationStop(BaseModel):
    """Schema for stopping a medication"""
    reason: Optional[str] = None


class PatientMedicationResponse(BaseModel):
    """Schema for patient medication response"""
    id: int
    patient_id: int
    medication_id: int
    dosage: str
    instructions: Optional[str]
    times_per_day: int
    start_date: date
    end_date: Optional[date]
    status: MedicationStatusEnum
    confirmed_by_patient: bool
    assigned_by_doctor: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Include medication details
    medication: Optional[MedicationResponse] = None
    
    class Config:
        from_attributes = True


# ==================== INACTIVE MEDICATION SCHEMAS ====================

class InactiveMedicationResponse(BaseModel):
    """Schema for inactive medication response"""
    id: int
    patient_medication_id: int
    stopped_by: int
    stopped_at: datetime
    reason: Optional[str]
    
    # Include the medication assignment details
    patient_medication: Optional[PatientMedicationResponse] = None
    
    class Config:
        from_attributes = True


# ==================== USER BASIC INFO ====================

class UserBasicInfo(BaseModel):
    """Basic user info for responses"""
    id: int
    full_name: str
    email: str
    
    class Config:
        from_attributes = True


# ==================== DETAILED RESPONSE WITH USER INFO ====================

class PatientMedicationDetailedResponse(BaseModel):
    """Detailed patient medication response with user info"""
    id: int
    patient_id: int
    medication_id: int
    dosage: str
    instructions: Optional[str]
    times_per_day: int
    start_date: date
    end_date: Optional[date]
    status: MedicationStatusEnum
    confirmed_by_patient: bool
    assigned_by_doctor: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Include full details
    medication: Optional[MedicationResponse] = None
    patient: Optional[UserBasicInfo] = None
    assigning_doctor: Optional[UserBasicInfo] = None
    
    class Config:
        from_attributes = True
