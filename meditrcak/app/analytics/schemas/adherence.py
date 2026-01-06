"""
Adherence analytics schemas
Pydantic models for adherence analytics responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class AdherenceOverview(BaseModel):
    """Overall adherence statistics"""
    total_patients: int = Field(..., description="Total number of patients with medications")
    patients_with_logs: int = Field(..., description="Patients who have medication logs")
    average_adherence_rate: float = Field(..., description="Average adherence rate across all patients (0-100)")
    adherence_distribution: dict = Field(..., description="Distribution of adherence rates (excellent: >90%, good: 70-90%, poor: <70%)")
    total_doses_scheduled: int = Field(..., description="Total doses scheduled in the period")
    total_doses_taken: int = Field(..., description="Total doses taken")
    total_doses_missed: int = Field(..., description="Total doses missed")
    total_doses_skipped: int = Field(..., description="Total doses skipped")
    period_start: date
    period_end: date


class AdherenceTrend(BaseModel):
    """Adherence trend data point"""
    date: date
    adherence_rate: float = Field(..., description="Adherence rate for this date (0-100)")
    doses_scheduled: int
    doses_taken: int
    doses_missed: int
    doses_skipped: int


class PatientAdherenceSummary(BaseModel):
    """Adherence summary for a specific patient"""
    patient_id: int
    patient_name: str
    adherence_rate: float = Field(..., description="Patient's overall adherence rate (0-100)")
    total_medications: int = Field(..., description="Number of active medications")
    doses_scheduled: int = Field(..., description="Total doses scheduled")
    doses_taken: int = Field(..., description="Total doses taken")
    doses_missed: int = Field(..., description="Total doses missed")
    doses_skipped: int = Field(..., description="Total doses skipped")
    last_log_date: Optional[date] = Field(None, description="Date of last medication log")


class MedicationAdherenceDetail(BaseModel):
    """Adherence details for a specific medication"""
    medication_id: int
    medication_name: str
    total_patients: int = Field(..., description="Number of patients taking this medication")
    average_adherence_rate: float = Field(..., description="Average adherence rate for this medication (0-100)")
    doses_scheduled: int
    doses_taken: int
    doses_missed: int
    doses_skipped: int
    most_common_skip_reason: Optional[str] = Field(None, description="Most common reason for skipping this medication")


class AdherenceStats(BaseModel):
    """Detailed adherence statistics"""
    overall_adherence: float = Field(..., description="Overall adherence rate (0-100)")
    on_time_adherence: float = Field(..., description="Adherence rate for doses taken on time (0-100)")
    weekday_adherence: float = Field(..., description="Adherence rate on weekdays (0-100)")
    weekend_adherence: float = Field(..., description="Adherence rate on weekends (0-100)")
    adherence_by_hour: dict = Field(..., description="Adherence rate by hour of day")
    adherence_by_day: dict = Field(..., description="Adherence rate by day of week")
    improvement_trend: float = Field(..., description="Adherence improvement trend (percentage points per week)")
    consistency_score: float = Field(..., description="Consistency score (0-100, higher = more consistent)")


class AnalyticsDashboardOverview(BaseModel):
    """Dashboard overview metrics"""
    total_patients: int
    total_medications: int
    average_adherence: float
    total_doses_today: int


class AnalyticsDashboard(BaseModel):
    """Comprehensive analytics dashboard data"""
    overview: AnalyticsDashboardOverview
    trends: List[AdherenceTrend]
    top_patients: List[PatientAdherenceSummary]