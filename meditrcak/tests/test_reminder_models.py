"""
Unit tests for reminder models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base
from app.reminders.models import (
    Reminder,
    ReminderSchedule,
    ReminderStatusEnum,
    ReminderChannelEnum,
    ReminderFrequencyEnum,
    WhatsAppMessage,
    NotificationPreference
)


@pytest.fixture
def test_db():
    """Create in-memory test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestReminderModel:
    """Test Reminder model"""

    def test_reminder_creation(self, test_db):
        """Test creating a reminder instance"""
        reminder = Reminder(
            patient_medication_id=1,
            patient_id=1,
            scheduled_time=datetime.now(),
            actual_dose_time=datetime.now() + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder message"
        )

        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        assert reminder.id is not None
        assert reminder.patient_medication_id == 1
        assert reminder.patient_id == 1
        assert reminder.status == ReminderStatusEnum.pending
        assert reminder.channel == ReminderChannelEnum.whatsapp
        assert reminder.message_text == "Test reminder message"
        assert reminder.retry_count == 0

    def test_reminder_repr(self, test_db):
        """Test reminder string representation"""
        reminder = Reminder(
            patient_medication_id=1,
            patient_id=1,
            scheduled_time=datetime(2025, 12, 23, 10, 0, 0),
            actual_dose_time=datetime(2025, 12, 23, 10, 15, 0),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder"
        )

        expected_repr = "<Reminder(id=None, patient_id=1, status=pending, time=2025-12-23 10:00:00)>"
        assert repr(reminder) == expected_repr


class TestReminderScheduleModel:
    """Test ReminderSchedule model"""

    def test_schedule_creation(self, test_db):
        """Test creating a reminder schedule"""
        schedule = ReminderSchedule(
            patient_medication_id=1,
            patient_id=1,
            is_active=True,
            frequency=ReminderFrequencyEnum.daily,
            reminder_times='["08:00", "20:00"]',
            advance_minutes=15,
            channel_whatsapp=True,
            channel_sms=False,
            channel_push=True,
            channel_email=False,
            auto_skip_if_taken=True,
            escalate_if_missed=True,
            escalate_delay_minutes=30,
            quiet_hours_enabled=False,
            start_date=datetime.now(),
            end_date=None
        )

        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        assert schedule.id is not None
        assert schedule.patient_medication_id == 1
        assert schedule.patient_id == 1
        assert schedule.is_active == True
        assert schedule.frequency == ReminderFrequencyEnum.daily
        assert schedule.advance_minutes == 15
        assert schedule.channel_whatsapp == True

    def test_schedule_repr(self, test_db):
        """Test schedule string representation"""
        schedule = ReminderSchedule(
            patient_medication_id=1,
            patient_id=1,
            is_active=True,
            frequency=ReminderFrequencyEnum.daily,
            reminder_times='["08:00"]',
            advance_minutes=15,
            channel_whatsapp=True,
            channel_sms=False,
            channel_push=True,
            channel_email=False,
            auto_skip_if_taken=True,
            escalate_if_missed=True,
            escalate_delay_minutes=30,
            quiet_hours_enabled=False,
            start_date=datetime.now(),
            end_date=None
        )

        expected_repr = "<ReminderSchedule(id=None, patient_medication_id=1, active=True)>"
        assert repr(schedule) == expected_repr


class TestWhatsAppMessageModel:
    """Test WhatsAppMessage model"""

    def test_whatsapp_message_creation(self, test_db):
        """Test creating a WhatsApp message"""
        message = WhatsAppMessage(
            patient_id=1,
            direction="outbound",
            message_type="text",
            twilio_message_sid="SM123456789",
            from_number="whatsapp:+1234567890",
            to_number="whatsapp:+0987654321",
            body="Test WhatsApp message",
            status="sent",
            is_processed=False
        )

        test_db.add(message)
        test_db.commit()
        test_db.refresh(message)

        assert message.id is not None
        assert message.patient_id == 1
        assert message.direction == "outbound"
        assert message.twilio_message_sid == "SM123456789"
        assert message.is_processed == False

    def test_whatsapp_message_repr(self, test_db):
        """Test WhatsApp message string representation"""
        message = WhatsAppMessage(
            patient_id=1,
            direction="outbound",
            message_type="text",
            twilio_message_sid="SM123456789",
            from_number="whatsapp:+1234567890",
            to_number="whatsapp:+0987654321",
            body="Test message",
            status="sent",
            is_processed=False
        )

        expected_repr = "<WhatsAppMessage(id=None, direction=outbound, sid=SM123456789)>"
        assert repr(message) == expected_repr


class TestNotificationPreferenceModel:
    """Test NotificationPreference model"""

    def test_notification_preference_creation(self, test_db):
        """Test creating notification preferences"""
        prefs = NotificationPreference(
            patient_id=1,
            whatsapp_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            email_enabled=False,
            whatsapp_number="+1234567890",
            sms_number=None,
            email_address=None,
            default_advance_minutes=15,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
            max_reminders_per_day=10,
            consolidate_reminders=False,
            preferred_language="en"
        )

        test_db.add(prefs)
        test_db.commit()
        test_db.refresh(prefs)

        assert prefs.id is not None
        assert prefs.patient_id == 1
        assert prefs.whatsapp_enabled == True
        assert prefs.sms_enabled == False
        assert prefs.preferred_language == "en"

    def test_notification_preference_repr(self, test_db):
        """Test notification preference string representation"""
        prefs = NotificationPreference(
            patient_id=1,
            whatsapp_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            email_enabled=False,
            whatsapp_number="+1234567890",
            sms_number=None,
            email_address=None,
            default_advance_minutes=15,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
            max_reminders_per_day=10,
            consolidate_reminders=False,
            preferred_language="en"
        )

        expected_repr = "<NotificationPreference(patient_id=1, whatsapp=True)>"
        assert repr(prefs) == expected_repr


class TestEnums:
    """Test enum values"""

    def test_reminder_status_enum(self):
        """Test reminder status enum values"""
        assert ReminderStatusEnum.pending.value == "pending"
        assert ReminderStatusEnum.sent.value == "sent"
        assert ReminderStatusEnum.delivered.value == "delivered"
        assert ReminderStatusEnum.responded.value == "responded"
        assert ReminderStatusEnum.failed.value == "failed"
        assert ReminderStatusEnum.cancelled.value == "cancelled"

    def test_reminder_channel_enum(self):
        """Test reminder channel enum values"""
        assert ReminderChannelEnum.push.value == "push"
        assert ReminderChannelEnum.email.value == "email"
        assert ReminderChannelEnum.sms.value == "sms"
        assert ReminderChannelEnum.whatsapp.value == "whatsapp"
        assert ReminderChannelEnum.all.value == "all"

    def test_reminder_frequency_enum(self):
        """Test reminder frequency enum values"""
        assert ReminderFrequencyEnum.once.value == "once"
        assert ReminderFrequencyEnum.daily.value == "daily"
        assert ReminderFrequencyEnum.twice_daily.value == "twice_daily"
        assert ReminderFrequencyEnum.three_times_daily.value == "three_times_daily"
        assert ReminderFrequencyEnum.custom.value == "custom"