"""
Reminder and notification models
Support for scheduled reminders and WhatsApp/SMS integration
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.db import Base


class ReminderFrequencyEnum(str, enum.Enum):
    """How often reminder repeats"""
    once = "once"
    daily = "daily"
    twice_daily = "twice_daily"
    three_times_daily = "three_times_daily"
    custom = "custom"  # Custom schedule with specific times


class ReminderChannelEnum(str, enum.Enum):
    """Notification delivery channel"""
    push = "push"  # Push notification
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    all = "all"  # Send via all enabled channels


class ReminderStatusEnum(str, enum.Enum):
    """Current status of reminder"""
    pending = "pending"  # Scheduled, not yet sent
    sent = "sent"  # Successfully sent
    delivered = "delivered"  # Confirmed delivery (Twilio status)
    read = "read"  # Message read (WhatsApp read receipt)
    responded = "responded"  # Patient responded (taken/skipped)
    failed = "failed"  # Failed to send
    cancelled = "cancelled"  # Cancelled before sending


class Reminder(Base):
    """
    Individual reminder instance
    Each scheduled dose gets a reminder record
    """
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Schedule details
    scheduled_time = Column(DateTime, nullable=False, index=True)  # When to send reminder
    reminder_advance_minutes = Column(Integer, default=15)  # Send X minutes before dose time
    actual_dose_time = Column(DateTime, nullable=False)  # Actual medication time
    
    # Delivery details
    channel = Column(SQLEnum(ReminderChannelEnum), default=ReminderChannelEnum.whatsapp)
    status = Column(SQLEnum(ReminderStatusEnum), default=ReminderStatusEnum.pending, index=True)
    
    # Twilio tracking
    twilio_message_sid = Column(String(100), nullable=True, unique=True)  # Twilio message ID
    twilio_status = Column(String(50), nullable=True)  # queued, sent, delivered, failed
    twilio_error_code = Column(String(20), nullable=True)
    twilio_error_message = Column(Text, nullable=True)
    
    # Message content
    message_text = Column(Text, nullable=False)  # Actual message sent
    response_text = Column(Text, nullable=True)  # Patient's response
    response_received_at = Column(DateTime, nullable=True)
    
    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime, nullable=True)
    
    # Relationships to adherence
    medication_log_id = Column(Integer, ForeignKey("medication_logs.id"), nullable=True)  # Created log entry
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_medication = relationship("PatientMedication", back_populates="reminders")
    patient = relationship("User", foreign_keys=[patient_id])
    logs = relationship("MedicationLog", foreign_keys="[MedicationLog.reminder_id]", back_populates="reminder")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, patient_id={self.patient_id}, status={self.status}, time={self.scheduled_time})>"


class ReminderSchedule(Base):
    """
    Recurring reminder configuration for a patient medication
    Defines when and how reminders should be sent
    """
    __tablename__ = "reminder_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_medication_id = Column(Integer, ForeignKey("patient_medications.id"), nullable=False, unique=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Schedule configuration
    is_active = Column(Boolean, default=True)
    frequency = Column(SQLEnum(ReminderFrequencyEnum), default=ReminderFrequencyEnum.daily)
    
    # Timing
    reminder_times = Column(JSON, nullable=False)  # List of times: ["08:00", "20:00"]
    advance_minutes = Column(Integer, default=15)  # Send reminder X minutes before
    
    # Channels (can enable multiple)
    channel_whatsapp = Column(Boolean, default=True)
    channel_sms = Column(Boolean, default=False)
    channel_push = Column(Boolean, default=True)
    channel_email = Column(Boolean, default=False)
    
    # Smart features
    auto_skip_if_taken = Column(Boolean, default=True)  # Don't send if already logged as taken
    escalate_if_missed = Column(Boolean, default=True)  # Send follow-up if missed
    escalate_delay_minutes = Column(Integer, default=30)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)  # "07:00"
    
    # Date range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # Null = indefinite
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_medication = relationship("PatientMedication", back_populates="reminder_schedule")
    patient = relationship("User", foreign_keys=[patient_id])
    
    def __repr__(self):
        return f"<ReminderSchedule(id={self.id}, patient_medication_id={self.patient_medication_id}, active={self.is_active})>"


class WhatsAppMessage(Base):
    """
    WhatsApp message log for audit and debugging
    Stores all WhatsApp interactions
    """
    __tablename__ = "whatsapp_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=True)
    
    # Message details
    direction = Column(String(10), nullable=False)  # inbound, outbound
    message_type = Column(String(20), default="text")  # text, image, location
    
    # Twilio details
    twilio_message_sid = Column(String(100), unique=True, index=True)
    from_number = Column(String(20), nullable=False)  # WhatsApp:+1234567890
    to_number = Column(String(20), nullable=False)
    
    # Content
    body = Column(Text, nullable=True)  # Message text
    media_url = Column(Text, nullable=True)  # Media URL if any
    
    # Status
    status = Column(String(20), nullable=True)  # Twilio status
    error_code = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing
    is_processed = Column(Boolean, default=False)  # Whether we've handled this message
    processed_at = Column(DateTime, nullable=True)
    processed_action = Column(String(50), nullable=True)  # taken, skipped, unknown
    
    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    reminder = relationship("Reminder", foreign_keys=[reminder_id])
    
    def __repr__(self):
        return f"<WhatsAppMessage(id={self.id}, direction={self.direction}, sid={self.twilio_message_sid})>"


class NotificationPreference(Base):
    """
    Patient notification preferences
    Controls when and how to send reminders
    """
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Channel enablement
    whatsapp_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    
    # Contact info
    whatsapp_number = Column(String(20), nullable=True)  # E.164 format: +1234567890
    sms_number = Column(String(20), nullable=True)
    email_address = Column(String(100), nullable=True)
    
    # Timing preferences
    default_advance_minutes = Column(Integer, default=15)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="07:00")
    
    # Frequency control
    max_reminders_per_day = Column(Integer, default=10)
    consolidate_reminders = Column(Boolean, default=False)  # Group nearby reminders
    
    # Language
    preferred_language = Column(String(5), default="en")  # en, es, fr, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    
    def __repr__(self):
        return f"<NotificationPreference(patient_id={self.patient_id}, whatsapp={self.whatsapp_enabled})>"
