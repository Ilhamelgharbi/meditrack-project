"""
Unit tests for reminder services
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base
from app.reminders.services import ReminderService
from app.reminders.models import (
    Reminder,
    ReminderSchedule,
    ReminderStatusEnum,
    ReminderChannelEnum,
    ReminderFrequencyEnum
)
from app.reminders.schemas import (
    ReminderScheduleCreate,
    ReminderScheduleUpdate
)
from app.medications.models import PatientMedication, Medication
from app.adherence.models import MedicationLog


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


@pytest.fixture
def reminder_service(test_db):
    """Create reminder service instance"""
    return ReminderService(test_db)


@pytest.fixture
def sample_patient_medication(test_db):
    """Create sample patient medication"""
    # First create a medication
    medication = Medication(
        name="Test Medication",
        form="tablet",
        default_dosage="10mg",
        created_by=1  # Required field
    )
    test_db.add(medication)
    test_db.commit()
    test_db.refresh(medication)
    
    # Then create patient medication
    med = PatientMedication(
        patient_id=1,
        medication_id=medication.id,
        dosage="10mg",
        instructions="Take once daily",
        times_per_day=1,
        start_date=datetime.now(),
        end_date=None,
        status="active",
        confirmed_by_patient=True,
        assigned_by_doctor=1  # Required field - doctor who assigned the medication
    )
    test_db.add(med)
    test_db.commit()
    test_db.refresh(med)
    return med


class TestReminderService:
    """Test ReminderService methods"""

    def test_create_reminder_schedule_success(self, reminder_service, test_db, sample_patient_medication):
        """Test successful creation of reminder schedule"""
        schedule_data = ReminderScheduleCreate(
            patient_medication_id=sample_patient_medication.id,
            frequency="daily",
            reminder_times=["08:00", "20:00"],
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

        with patch.object(reminder_service, 'generate_reminders_for_schedule') as mock_generate:
            mock_generate.return_value = []
            schedule = reminder_service.create_reminder_schedule(
                patient_id=1,
                schedule_data=schedule_data
            )

        assert schedule.patient_medication_id == sample_patient_medication.id
        assert schedule.patient_id == 1
        assert schedule.is_active == True
        assert schedule.frequency == "daily"
        assert schedule.advance_minutes == 15
        assert schedule.channel_whatsapp == True

    def test_create_reminder_schedule_patient_medication_not_found(self, reminder_service):
        """Test creating schedule with non-existent patient medication"""
        schedule_data = ReminderScheduleCreate(
            patient_medication_id=999,
            frequency="daily",
            reminder_times=["08:00"],
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

        with pytest.raises(ValueError, match="Patient medication not found or access denied"):
            reminder_service.create_reminder_schedule(
                patient_id=1,
                schedule_data=schedule_data
            )

    def test_create_reminder_schedule_already_exists(self, reminder_service, test_db, sample_patient_medication):
        """Test creating schedule when one already exists"""
        # Create existing schedule
        existing_schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
        test_db.add(existing_schedule)
        test_db.commit()

        schedule_data = ReminderScheduleCreate(
            patient_medication_id=sample_patient_medication.id,
            frequency="daily",
            reminder_times=["08:00"],
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

        with pytest.raises(ValueError, match="Reminder schedule already exists for this medication"):
            reminder_service.create_reminder_schedule(
                patient_id=1,
                schedule_data=schedule_data
            )

    def test_get_reminder_schedule_success(self, reminder_service, test_db, sample_patient_medication):
        """Test getting reminder schedule successfully"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        result = reminder_service.get_reminder_schedule(
            patient_id=1,
            patient_medication_id=sample_patient_medication.id
        )

        assert result is not None
        assert result.id == schedule.id
        assert result.patient_medication_id == sample_patient_medication.id

    def test_get_patient_reminder_schedules(self, reminder_service, test_db, sample_patient_medication):
        """Test getting all patient reminder schedules"""
        # Create multiple schedules
        schedule1 = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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

        # Create another medication
        medication2 = Medication(
            name="Test Medication 2",
            form="capsule",
            default_dosage="20mg",
            created_by=1
        )
        test_db.add(medication2)
        test_db.commit()
        test_db.refresh(medication2)

        # Create another patient medication for the same patient
        med2 = PatientMedication(
            patient_id=1,
            medication_id=medication2.id,
            dosage="20mg",
            instructions="Take twice daily",
            times_per_day=2,
            start_date=datetime.now(),
            end_date=None,
            status="active",
            confirmed_by_patient=True,
            assigned_by_doctor=1  # Required field
        )
        test_db.add(med2)
        test_db.commit()

        schedule2 = ReminderSchedule(
            patient_medication_id=med2.id,
            patient_id=1,
            is_active=False,  # Inactive
            frequency="twice_daily",
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

        test_db.add(schedule1)
        test_db.add(schedule2)
        test_db.commit()

        # Test getting all schedules
        all_schedules = reminder_service.get_patient_reminder_schedules(patient_id=1)
        assert len(all_schedules) == 2

        # Test getting only active schedules
        active_schedules = reminder_service.get_patient_reminder_schedules(
            patient_id=1,
            active_only=True
        )
        assert len(active_schedules) == 1
        assert active_schedules[0].is_active == True

    def test_update_reminder_schedule_success(self, reminder_service, test_db, sample_patient_medication):
        """Test updating reminder schedule successfully"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        update_data = ReminderScheduleUpdate(
            advance_minutes=30,
            channel_sms=True,
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )

        updated_schedule = reminder_service.update_reminder_schedule(
            patient_id=1,
            schedule_id=schedule.id,
            update_data=update_data
        )

        assert updated_schedule.advance_minutes == 30
        assert updated_schedule.channel_sms == True
        assert updated_schedule.quiet_hours_enabled == True
        assert updated_schedule.quiet_hours_start == "22:00"
        assert updated_schedule.quiet_hours_end == "07:00"

    def test_delete_reminder_schedule_success(self, reminder_service, test_db, sample_patient_medication):
        """Test deleting reminder schedule successfully"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        result = reminder_service.delete_reminder_schedule(
            patient_id=1,
            schedule_id=schedule.id
        )

        assert result == True

        # Verify schedule is deleted
        deleted_schedule = test_db.query(ReminderSchedule).filter(
            ReminderSchedule.id == schedule.id
        ).first()
        assert deleted_schedule is None

    def test_toggle_reminder_schedule(self, reminder_service, test_db, sample_patient_medication):
        """Test toggling reminder schedule active status"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        # Toggle to inactive
        toggled_schedule = reminder_service.toggle_reminder_schedule(
            patient_id=1,
            schedule_id=schedule.id,
            is_active=False
        )

        assert toggled_schedule.is_active == False

        # Toggle back to active
        toggled_schedule = reminder_service.toggle_reminder_schedule(
            patient_id=1,
            schedule_id=schedule.id,
            is_active=True
        )

        assert toggled_schedule.is_active == True

    def test_create_individual_reminder_success(self, reminder_service, test_db, sample_patient_medication):
        """Test creating individual reminder successfully"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        reminder = reminder_service.create_individual_reminder(
            patient_id=1,
            patient_medication_id=sample_patient_medication.id,
            scheduled_time=scheduled_time,
            message_text="Custom reminder message"
        )

        assert reminder.patient_medication_id == sample_patient_medication.id
        assert reminder.patient_id == 1
        assert reminder.scheduled_time == scheduled_time
        assert reminder.message_text == "Custom reminder message"
        assert reminder.status == ReminderStatusEnum.pending

    def test_create_individual_reminder_already_exists(self, reminder_service, test_db, sample_patient_medication):
        """Test creating reminder that already exists"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        # Create first reminder
        reminder_service.create_individual_reminder(
            patient_id=1,
            patient_medication_id=sample_patient_medication.id,
            scheduled_time=scheduled_time
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="Reminder already exists for this medication at this time"):
            reminder_service.create_individual_reminder(
                patient_id=1,
                patient_medication_id=sample_patient_medication.id,
                scheduled_time=scheduled_time
            )

    def test_get_pending_reminders(self, reminder_service, test_db, sample_patient_medication):
        """Test getting pending reminders"""
        # Create past reminder (should be picked up)
        past_time = datetime.now() - timedelta(minutes=5)
        past_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=past_time,
            actual_dose_time=past_time + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Past reminder"
        )

        # Create future reminder (should not be picked up)
        future_time = datetime.now() + timedelta(hours=1)
        future_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=future_time,
            actual_dose_time=future_time + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Future reminder"
        )

        # Create sent reminder (should not be picked up)
        sent_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=past_time,
            actual_dose_time=past_time + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,
            message_text="Sent reminder"
        )

        test_db.add(past_reminder)
        test_db.add(future_reminder)
        test_db.add(sent_reminder)
        test_db.commit()

        pending_reminders = reminder_service.get_pending_reminders()

        assert len(pending_reminders) == 1
        assert pending_reminders[0].message_text == "Past reminder"

    def test_cancel_reminder_success(self, reminder_service, test_db, sample_patient_medication):
        """Test canceling pending reminder successfully"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() + timedelta(hours=1),
            actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder"
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        canceled_reminder = reminder_service.cancel_reminder(
            patient_id=1,
            reminder_id=reminder.id,
            reason="Patient request"
        )

        assert canceled_reminder.status == ReminderStatusEnum.cancelled
        assert canceled_reminder.response_text == "Patient request"

    def test_cancel_reminder_not_pending(self, reminder_service, test_db, sample_patient_medication):
        """Test canceling non-pending reminder fails"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() + timedelta(hours=1),
            actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,  # Already sent
            message_text="Test reminder"
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        with pytest.raises(ValueError, match="Can only cancel pending reminders"):
            reminder_service.cancel_reminder(
                patient_id=1,
                reminder_id=reminder.id
            )

    def test_mark_reminder_sent(self, reminder_service, test_db, sample_patient_medication):
        """Test marking reminder as sent"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now(),
            actual_dose_time=datetime.now() + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder"
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        sent_reminder = reminder_service.mark_reminder_sent(
            reminder_id=reminder.id,
            channel="whatsapp",
            message_sid="SM123456789"
        )

        assert sent_reminder.status == ReminderStatusEnum.sent
        assert sent_reminder.sent_at is not None
        assert sent_reminder.twilio_message_sid == "SM123456789"

    def test_get_reminder_stats(self, reminder_service, test_db, sample_patient_medication):
        """Test getting reminder statistics"""
        base_time = datetime.now() - timedelta(days=10)

        # Create various reminders
        reminders_data = [
            (ReminderStatusEnum.sent, base_time + timedelta(days=1)),
            (ReminderStatusEnum.sent, base_time + timedelta(days=2)),
            (ReminderStatusEnum.delivered, base_time + timedelta(days=3)),
            (ReminderStatusEnum.delivered, base_time + timedelta(days=4)),
            (ReminderStatusEnum.responded, base_time + timedelta(days=5)),
            (ReminderStatusEnum.responded, base_time + timedelta(days=6)),
            (ReminderStatusEnum.failed, base_time + timedelta(days=7)),
            (ReminderStatusEnum.pending, base_time + timedelta(days=8)),  # Within 30 days
        ]

        for status, scheduled_time in reminders_data:
            reminder = Reminder(
                patient_medication_id=sample_patient_medication.id,
                patient_id=1,
                scheduled_time=scheduled_time,
                actual_dose_time=scheduled_time + timedelta(minutes=15),
                reminder_advance_minutes=15,
                channel=ReminderChannelEnum.whatsapp,
                status=status,
                message_text="Test reminder"
            )
            test_db.add(reminder)

        test_db.commit()

        stats = reminder_service.get_reminder_stats(patient_id=1, days=30)

        assert stats["total_scheduled"] == 8
        assert stats["sent"] == 2
        assert stats["delivered"] == 2
        assert stats["responded"] == 2
        assert stats["failed"] == 1
        assert stats["delivery_rate"] == 25.0  # 2/8 * 100 (delivered count)
        assert stats["response_rate"] == 100.0  # 2/2 * 100