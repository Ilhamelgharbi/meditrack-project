from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


# Enums
class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class StatusEnum(str, Enum):
    stable = "stable"
    critical = "critical"
    under_observation = "under_observation"


# Patient Create Schema (when registering as patient)
class PatientCreate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    blood_type: Optional[str] = Field(None, max_length=5)
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    medical_history: Optional[str] = Field(None, max_length=2000)
    allergies: Optional[str] = Field(None, max_length=500)


# Patient Update Schema (patient can update own info)
class PatientUpdate(BaseModel):
    # User fields
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    # Patient fields
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    blood_type: Optional[str] = Field(None, max_length=5)
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    medical_history: Optional[str] = Field(None, max_length=2000)
    allergies: Optional[str] = Field(None, max_length=500)
    current_medications: Optional[str] = Field(None, max_length=1000)


# Admin Update Schema (admin can update all patient fields including status)
class PatientAdminUpdate(BaseModel):
    # User fields
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    # Patient fields
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    blood_type: Optional[str] = Field(None, max_length=5)
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    status: Optional[StatusEnum] = None
    medical_history: Optional[str] = Field(None, max_length=2000)
    allergies: Optional[str] = Field(None, max_length=500)
    current_medications: Optional[str] = Field(None, max_length=1000)
    assigned_admin_id: Optional[int] = None


# Patient Response Schema
class PatientResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[date]
    gender: Optional[GenderEnum]
    blood_type: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    status: StatusEnum
    medical_history: Optional[str]
    allergies: Optional[str]
    current_medications: Optional[str]
    assigned_admin_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Include user info
    user: Optional["UserBasicInfo"] = None
    
    class Config:
        from_attributes = True


# User Basic Info for Patient Response
class UserBasicInfo(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: str
    
    class Config:
        from_attributes = True
