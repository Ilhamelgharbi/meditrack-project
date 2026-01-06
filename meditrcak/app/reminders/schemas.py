"""
Reminder and notification schemas
Request/response models for reminder management and Twilio integration
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, time
from enum import Enum


class ReminderFrequency(str, Enum):
    """Reminder frequency options"""
    once = "once"
    daily = "daily"
    twice_daily = "twice_daily"
    three_times_daily = "three_times_daily"
    custom = "custom"


class ReminderChannel(str, Enum):
    """Notification channels"""
    push = "push"
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    all = "all"


class ReminderStatus(str, Enum):
    """Reminder delivery status"""
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    responded = "responded"
    failed = "failed"
    cancelled = "cancelled"


# ==================== REMINDER SCHEMAS ====================

class ReminderResponse(BaseModel):
    """Single reminder instance response"""
    id: int
    patient_medication_id: int
    patient_id: int
    scheduled_time: datetime
    actual_dose_time: datetime
    reminder_advance_minutes: int
    channel: str
    status: str
    twilio_message_sid: Optional[str]
    twilio_status: Optional[str]
    message_text: str
    response_text: Optional[str]
    response_received_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    retry_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReminderDetailed(ReminderResponse):
    """Reminder with medication details"""
    medication_name: str
    medication_dosage: str
    patient_name: str


class ReminderCancel(BaseModel):
    """Cancel a scheduled reminder"""
    reason: Optional[str] = None


# ==================== REMINDER SCHEDULE SCHEMAS ====================

class ReminderScheduleCreate(BaseModel):
    """Create reminder schedule for patient medication"""
    patient_medication_id: int
    frequency: ReminderFrequency = ReminderFrequency.daily
    reminder_times: List[str] = Field(..., description="Times in HH:MM format, e.g., ['08:00', '20:00']")
    advance_minutes: int = Field(default=15, ge=0, le=120)
    
    # Channels
    channel_whatsapp: bool = True
    channel_sms: bool = False
    channel_push: bool = True
    channel_email: bool = False
    
    # Smart features
    auto_skip_if_taken: bool = True
    escalate_if_missed: bool = True
    escalate_delay_minutes: int = Field(default=30, ge=5, le=240)
    
    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(None, description="HH:MM format")
    
    # Date range
    start_date: datetime
    end_date: Optional[datetime] = None
    
    @validator('reminder_times')
    def validate_times(cls, v):
        """Validate time format"""
        for t in v:
            try:
                datetime.strptime(t, "%H:%M")
            except ValueError:
                raise ValueError(f"Invalid time format: {t}. Use HH:MM format")
        return v
    
    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_quiet_hours(cls, v):
        """Validate quiet hours format"""
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError(f"Invalid time format: {v}. Use HH:MM format")
        return v


class ReminderScheduleUpdate(BaseModel):
    """Update reminder schedule"""
    is_active: Optional[bool] = None
    frequency: Optional[ReminderFrequency] = None
    reminder_times: Optional[List[str]] = None
    advance_minutes: Optional[int] = Field(None, ge=0, le=120)
    channel_whatsapp: Optional[bool] = None
    channel_sms: Optional[bool] = None
    channel_push: Optional[bool] = None
    channel_email: Optional[bool] = None
    auto_skip_if_taken: Optional[bool] = None
    escalate_if_missed: Optional[bool] = None
    escalate_delay_minutes: Optional[int] = Field(None, ge=5, le=240)
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    end_date: Optional[datetime] = None


class PatientMedicationInfo(BaseModel):
    """Patient medication info for reminder schedules"""
    id: int
    medication_id: int
    dosage: str
    instructions: Optional[str]
    times_per_day: int
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    confirmed_by_patient: bool
    medication: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class ReminderScheduleResponse(BaseModel):
    """Reminder schedule response"""
    id: int
    patient_medication_id: int
    patient_id: int
    is_active: bool
    frequency: str
    reminder_times: List[str]
    advance_minutes: int
    channel_whatsapp: bool
    channel_sms: bool
    channel_push: bool
    channel_email: bool
    auto_skip_if_taken: bool
    escalate_if_missed: bool
    escalate_delay_minutes: int
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    patient_medication: Optional[PatientMedicationInfo] = None
    
    class Config:
        from_attributes = True


class ReminderScheduleDetailed(ReminderScheduleResponse):
    """Schedule with medication details"""
    medication_name: str
    medication_dosage: str
    medication_form: str


# ==================== WHATSAPP INTEGRATION ====================

class WhatsAppWebhook(BaseModel):
    """Incoming WhatsApp webhook from Twilio"""
    MessageSid: str
    From: str  # whatsapp:+1234567890
    To: str
    Body: str
    NumMedia: Optional[str] = "0"
    MediaUrl0: Optional[str] = None
    SmsStatus: Optional[str] = None
    
    class Config:
        populate_by_name = True


class WhatsAppMessageResponse(BaseModel):
    """WhatsApp message log response"""
    id: int
    patient_id: int
    reminder_id: Optional[int]
    direction: str  # inbound, outbound
    message_type: str
    twilio_message_sid: str
    from_number: str
    to_number: str
    body: Optional[str]
    media_url: Optional[str]
    status: Optional[str]
    is_processed: bool
    processed_at: Optional[datetime]
    processed_action: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    received_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class WhatsAppSendRequest(BaseModel):
    """Send WhatsApp message request"""
    patient_id: int
    message: str
    reminder_id: Optional[int] = None


class WhatsAppSendResponse(BaseModel):
    """WhatsApp send response"""
    success: bool
    message_sid: Optional[str]
    status: str
    error: Optional[str] = None


# ==================== NOTIFICATION PREFERENCES ====================

class NotificationPreferenceCreate(BaseModel):
    """Create notification preferences"""
    whatsapp_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    email_enabled: bool = False
    whatsapp_number: Optional[str] = Field(None, description="E.164 format: +1234567890")
    sms_number: Optional[str] = None
    email_address: Optional[str] = None
    default_advance_minutes: int = Field(default=15, ge=0, le=120)
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    max_reminders_per_day: int = Field(default=10, ge=1, le=50)
    consolidate_reminders: bool = False
    preferred_language: str = "en"


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences"""
    whatsapp_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    whatsapp_number: Optional[str] = None
    sms_number: Optional[str] = None
    email_address: Optional[str] = None
    default_advance_minutes: Optional[int] = Field(None, ge=0, le=120)
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    max_reminders_per_day: Optional[int] = Field(None, ge=1, le=50)
    consolidate_reminders: Optional[bool] = None
    preferred_language: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response"""
    id: int
    patient_id: int
    whatsapp_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    email_enabled: bool
    whatsapp_number: Optional[str]
    sms_number: Optional[str]
    email_address: Optional[str]
    default_advance_minutes: int
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    max_reminders_per_day: int
    consolidate_reminders: bool
    preferred_language: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== BULK OPERATIONS ====================

class BulkReminderGenerate(BaseModel):
    """Generate reminders for a date range"""
    patient_medication_id: int
    start_date: datetime
    end_date: datetime


class BulkReminderResponse(BaseModel):
    """Bulk reminder generation response"""
    generated_count: int
    reminder_ids: List[int]
    errors: List[str]


# ==================== DASHBOARD & REPORTS ====================

class ReminderDashboard(BaseModel):
    """Reminder dashboard for patient"""
    today_total: int
    today_sent: int
    today_pending: int
    today_responded: int
    upcoming_reminders: List[ReminderDetailed]
    recent_history: List[ReminderDetailed]
    active_schedules: List[ReminderScheduleDetailed]


class ReminderAnalytics(BaseModel):
    """Reminder analytics"""
    period_start: datetime
    period_end: datetime
    total_sent: int
    total_delivered: int
    total_responded: int
    response_rate: float
    average_response_time_minutes: float
    channel_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]
