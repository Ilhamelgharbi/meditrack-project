"""
Adherence tracking schemas
Request/response models for logging and tracking medication adherence
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class MedicationLogStatus(str, Enum):
    """Status options for medication log"""
    taken = "taken"
    skipped = "skipped"
    missed = "missed"


class LoggedVia(str, Enum):
    """How the log was created"""
    manual = "manual"
    whatsapp = "whatsapp"
    sms = "sms"
    auto = "auto"


# ==================== MEDICATION LOG SCHEMAS ====================

class MedicationLogCreate(BaseModel):
    """Create a new medication log entry"""
    patient_medication_id: int
    scheduled_time: datetime
    status: MedicationLogStatus
    actual_time: Optional[datetime] = None
    notes: Optional[str] = None
    skipped_reason: Optional[str] = None
    logged_via: LoggedVia = LoggedVia.manual
    
    @validator('actual_time')
    def validate_actual_time(cls, v, values):
        """Actual time required if status is taken"""
        if values.get('status') == MedicationLogStatus.taken and v is None:
            return datetime.now()
        return v
    
    @validator('skipped_reason')
    def validate_skipped_reason(cls, v, values):
        """Skipped reason recommended if status is skipped"""
        if values.get('status') == MedicationLogStatus.skipped and not v:
            return "No reason provided"
        return v


class MedicationLogUpdate(BaseModel):
    """Update existing log entry"""
    status: Optional[MedicationLogStatus] = None
    actual_time: Optional[datetime] = None
    notes: Optional[str] = None
    skipped_reason: Optional[str] = None


class MedicationLogResponse(BaseModel):
    """Medication log response"""
    id: int
    patient_medication_id: int
    patient_id: int
    scheduled_time: datetime
    scheduled_date: date
    status: str
    actual_time: Optional[datetime]
    on_time: bool
    minutes_late: Optional[int]
    notes: Optional[str]
    skipped_reason: Optional[str]
    logged_via: str
    reminder_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    medication_form: Optional[str] = None
    
    class Config:
        from_attributes = True


class MedicationLogDetailed(MedicationLogResponse):
    """Detailed log with medication info"""
    medication_name: str
    medication_dosage: str
    medication_form: str


# ==================== ADHERENCE STATS SCHEMAS ====================

class AdherenceStatsResponse(BaseModel):
    """Adherence statistics response"""
    id: int
    patient_id: int
    patient_medication_id: Optional[int]
    period_type: str  # daily, weekly, monthly, overall
    period_start: date
    period_end: date
    total_scheduled: int
    total_taken: int
    total_skipped: int
    total_missed: int
    adherence_score: float
    on_time_score: float
    current_streak: int
    longest_streak: int
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class AdherenceStatsDetailed(AdherenceStatsResponse):
    """Detailed stats with medication info"""
    medication_name: Optional[str] = None
    medication_dosage: Optional[str] = None


class AdherenceChartData(BaseModel):
    """Chart data for adherence visualization"""
    date: date
    score: float
    taken: int
    scheduled: int
    status: str  # excellent, good, fair, poor


class AdherenceDashboard(BaseModel):
    """Complete adherence dashboard data"""
    overall_stats: AdherenceStatsResponse
    weekly_stats: AdherenceStatsResponse
    daily_stats: AdherenceStatsResponse
    chart_data: List[AdherenceChartData]
    recent_logs: List[MedicationLogResponse]


# ==================== ADHERENCE GOAL SCHEMAS ====================

class AdherenceGoalCreate(BaseModel):
    """Create new adherence goal"""
    patient_medication_id: Optional[int] = None  # Null = overall goal
    target_adherence_score: float = Field(ge=0, le=100, default=80.0)
    target_streak_days: int = Field(ge=1, default=7)
    notes: Optional[str] = None


class AdherenceGoalUpdate(BaseModel):
    """Update adherence goal"""
    target_adherence_score: Optional[float] = Field(None, ge=0, le=100)
    target_streak_days: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None


class AdherenceGoalResponse(BaseModel):
    """Adherence goal response"""
    id: int
    patient_id: int
    patient_medication_id: Optional[int]
    target_adherence_score: float
    target_streak_days: int
    current_progress: float
    is_achieved: bool
    achieved_at: Optional[datetime]
    set_by: int
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== BULK OPERATIONS ====================

class BulkLogCreate(BaseModel):
    """Create multiple logs at once (e.g., from scheduled reminders)"""
    logs: List[MedicationLogCreate]


class BulkLogResponse(BaseModel):
    """Response for bulk log creation"""
    created_count: int
    failed_count: int
    created_ids: List[int]
    errors: List[str]


# ==================== ANALYTICS SCHEMAS ====================

class AdherenceReport(BaseModel):
    """Comprehensive adherence report"""
    patient_id: int
    report_period_start: date
    report_period_end: date
    summary: AdherenceStatsResponse
    daily_breakdown: List[AdherenceChartData]
    medication_breakdown: List[AdherenceStatsDetailed]
    insights: List[str]  # AI-generated insights
    recommendations: List[str]  # Improvement suggestions


class PatientAdherenceSummary(BaseModel):
    """Summary for doctor's patient list"""
    patient_id: int
    patient_name: str
    active_medications_count: int
    overall_adherence_score: float
    current_streak: int
    last_missed_date: Optional[date]
    status: str  # excellent, good, needs_attention, critical
