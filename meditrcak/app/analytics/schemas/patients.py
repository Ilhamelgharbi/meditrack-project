"""
Patient analytics schemas
Pydantic models for patient analytics responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class PatientDemographics(BaseModel):
    """Patient demographic statistics"""
    total_patients: int
    gender_distribution: Dict[str, int] = Field(..., description="Patient count by gender")
    age_distribution: Dict[str, int] = Field(..., description="Patient count by age groups")
    average_age: Optional[float] = Field(None, description="Average age of patients")
    blood_type_distribution: Dict[str, int] = Field(..., description="Patient count by blood type")
    registration_trend: Dict[str, int] = Field(..., description="New patient registrations by month")


class PatientStatusDistribution(BaseModel):
    """Distribution of patients by health status"""
    stable: int = Field(..., description="Number of patients with stable status")
    critical: int = Field(..., description="Number of patients with critical status")
    under_observation: int = Field(..., description="Number of patients under observation")
    total_patients: int
    status_percentages: Dict[str, float] = Field(..., description="Percentage distribution by status")


class PatientRegistrationTrend(BaseModel):
    """Patient registration trend data point"""
    date: date
    new_registrations: int
    cumulative_total: int


class PatientHealthMetrics(BaseModel):
    """Patient health metrics and statistics"""
    average_bmi: Optional[float] = Field(None, description="Average BMI of patients")
    bmi_distribution: Dict[str, int] = Field(..., description="BMI distribution (underweight, normal, overweight, obese)")
    patients_with_allergies: int = Field(..., description="Number of patients with recorded allergies")
    common_allergies: List[Dict[str, str]] = Field(..., description="Most common allergies")
    average_height: Optional[float] = Field(None, description="Average height in cm")
    average_weight: Optional[float] = Field(None, description="Average weight in kg")
    patients_with_medical_history: int = Field(..., description="Number of patients with medical history")


class PatientAnalyticsSummary(BaseModel):
    """Comprehensive patient analytics summary"""
    demographics: PatientDemographics
    status_distribution: PatientStatusDistribution
    health_metrics: PatientHealthMetrics
    recent_activity: Dict[str, int] = Field(..., description="Recent patient activity metrics")
    admin_workload: Dict[str, int] = Field(..., description="Admin workload distribution")