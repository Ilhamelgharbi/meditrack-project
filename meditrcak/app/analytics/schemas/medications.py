"""
Medication analytics schemas
Pydantic models for medication analytics responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class MedicationUsageStats(BaseModel):
    """Overall medication usage statistics"""
    total_medications: int = Field(..., description="Total medications in catalog")
    total_patient_medications: int = Field(..., description="Total patient-medication assignments")
    active_patient_medications: int = Field(..., description="Currently active patient-medication assignments")
    average_medications_per_patient: float = Field(..., description="Average number of medications per patient")
    most_common_forms: Dict[str, int] = Field(..., description="Usage count by medication form")
    prescriptions_by_doctor: Dict[str, int] = Field(..., description="Prescription count by doctor")


class MedicationPopularity(BaseModel):
    """Popularity data for a medication"""
    medication_id: int
    medication_name: str
    form: str
    total_prescriptions: int = Field(..., description="Total number of times prescribed")
    active_prescriptions: int = Field(..., description="Currently active prescriptions")
    unique_patients: int = Field(..., description="Number of unique patients")
    average_dosage: Optional[str] = Field(None, description="Most common dosage")
    created_by: str = Field(..., description="Doctor who added the medication")


class MedicationStatusDistribution(BaseModel):
    """Distribution of medications by status"""
    active: int = Field(..., description="Number of active medications")
    pending: int = Field(..., description="Number of pending medications")
    stopped: int = Field(..., description="Number of stopped medications")
    total: int
    status_percentages: Dict[str, float] = Field(..., description="Percentage distribution by status")


class TopPrescribedMedications(BaseModel):
    """Top prescribed medication data"""
    medication_id: int
    medication_name: str
    form: str
    prescriptions_count: int = Field(..., description="Number of prescriptions in the period")
    unique_patients: int = Field(..., description="Number of unique patients")
    average_daily_dosage: float = Field(..., description="Average times per day")
    most_common_doctor: Optional[str] = Field(None, description="Doctor who prescribes this most")


class MedicationAnalyticsSummary(BaseModel):
    """Comprehensive medication analytics summary"""
    usage_stats: MedicationUsageStats
    status_distribution: MedicationStatusDistribution
    top_medications: List[MedicationPopularity]
    recent_activity: Dict[str, int] = Field(..., description="Recent medication activity")
    prescription_trends: Dict[str, List[int]] = Field(..., description="Prescription trends over time")