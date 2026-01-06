"""
Comprehensive unit tests for ReminderService
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
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
def sample_medication(test_db):
    """Create sample medication"""
    # Create a user first (required for created_by)
    from app.auth.models import User
    user = User(
        email="doctor@test.com",
        password_hash="hashed",
        full_name="Test Doctor",
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    med = Medication(
        name="Aspirin",
        form="tablet",
        default_dosage="100mg",
        side_effects="May cause stomach irritation",
        warnings="Do not take with alcohol",
        created_by=user.id
    )
    test_db.add(med)
    test_db.commit()
    test_db.refresh(med)
    return med


@pytest.fixture
def sample_user(test_db):
    """Create sample user"""
    from app.auth.models import User
    user = User(
        email="patient@test.com",
        password_hash="hashed",
        full_name="Test Patient",
        role="patient"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_patient_medication(test_db, sample_medication, sample_user):
    """Create sample patient medication"""
    patient_med = PatientMedication(
        patient_id=sample_user.id,
        medication_id=sample_medication.id,
        dosage="100mg",
        instructions="Take once daily",
        times_per_day=1,
        start_date=datetime.now(),
        end_date=None,
        status="active",
        confirmed_by_patient=True,
        assigned_by_doctor=sample_user.id  # Use the same user as doctor
    )
    test_db.add(patient_med)
    test_db.commit()
    test_db.refresh(patient_med)
    return patient_med


class TestReminderServiceInit:
    """Test ReminderService initialization"""

    def test_init(self, test_db):
        """Test service initialization"""
        service = ReminderService(test_db)
        assert service.db == test_db


class TestReminderScheduleManagement:
    """Test reminder schedule management methods"""

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
                patient_id=sample_patient_medication.patient_id,
                schedule_data=schedule_data
            )

        assert schedule.patient_medication_id == sample_patient_medication.id
        assert schedule.patient_id == sample_patient_medication.patient_id
        assert schedule.is_active == True
        assert schedule.frequency == "daily"
        assert schedule.advance_minutes == 15
        assert schedule.channel_whatsapp == True
        assert json.loads(schedule.reminder_times) == ["08:00", "20:00"]

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
                patient_id=sample_patient_medication.patient_id,
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

    def test_get_reminder_schedule_not_found(self, reminder_service, sample_patient_medication):
        """Test getting reminder schedule that doesn't exist"""
        result = reminder_service.get_reminder_schedule(
            patient_id=1,
            patient_medication_id=sample_patient_medication.id
        )

        assert result is None

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

        # Create another patient medication for the same patient
        med2 = PatientMedication(
            patient_id=1,
            medication_id=2,
            dosage="20mg",
            instructions="Take twice daily",
            times_per_day=2,
            start_date=datetime.now(),
            end_date=None,
            status="active",
            confirmed_by_patient=True,
            assigned_by_doctor=1  # Add missing field
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

    def test_update_reminder_schedule_not_found(self, reminder_service):
        """Test updating non-existent reminder schedule"""
        update_data = ReminderScheduleUpdate(advance_minutes=30)

        with pytest.raises(ValueError, match="Reminder schedule not found or access denied"):
            reminder_service.update_reminder_schedule(
                patient_id=1,
                schedule_id=999,
                update_data=update_data
            )

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

    def test_delete_reminder_schedule_not_found(self, reminder_service):
        """Test deleting non-existent reminder schedule"""
        with pytest.raises(ValueError, match="Reminder schedule not found or access denied"):
            reminder_service.delete_reminder_schedule(
                patient_id=1,
                schedule_id=999
            )

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

    def test_toggle_reminder_schedule_not_found(self, reminder_service):
        """Test toggling non-existent reminder schedule"""
        with pytest.raises(ValueError, match="Reminder schedule not found or access denied"):
            reminder_service.toggle_reminder_schedule(
                patient_id=1,
                schedule_id=999,
                is_active=False
            )


class TestIndividualReminderManagement:
    """Test individual reminder management methods"""

    def test_create_individual_reminder_success(self, reminder_service, test_db, sample_patient_medication):
        """Test creating individual reminder successfully"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        reminder = reminder_service.create_individual_reminder(
            patient_id=sample_patient_medication.patient_id,
            patient_medication_id=sample_patient_medication.id,
            scheduled_time=scheduled_time,
            message_text="Custom reminder message"
        )

        assert reminder.patient_medication_id == sample_patient_medication.id
        assert reminder.patient_id == sample_patient_medication.patient_id
        assert reminder.scheduled_time == scheduled_time
        assert reminder.message_text == "Custom reminder message"
        assert reminder.status == ReminderStatusEnum.pending

    def test_create_individual_reminder_auto_message(self, reminder_service, test_db, sample_patient_medication):
        """Test creating individual reminder with auto-generated message"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        reminder = reminder_service.create_individual_reminder(
            patient_id=sample_patient_medication.patient_id,
            patient_medication_id=sample_patient_medication.id,
            scheduled_time=scheduled_time
        )

        assert reminder.patient_medication_id == sample_patient_medication.id
        assert reminder.patient_id == sample_patient_medication.patient_id
        assert reminder.scheduled_time == scheduled_time
        assert "Aspirin" in reminder.message_text
        assert "100mg" in reminder.message_text
        assert reminder.status == ReminderStatusEnum.pending

    def test_create_individual_reminder_patient_medication_not_found(self, reminder_service):
        """Test creating reminder with non-existent patient medication"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        with pytest.raises(ValueError, match="Patient medication not found or access denied"):
            reminder_service.create_individual_reminder(
                patient_id=1,
                patient_medication_id=999,
                scheduled_time=scheduled_time
            )

    def test_create_individual_reminder_already_exists(self, reminder_service, test_db, sample_patient_medication):
        """Test creating reminder that already exists"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        # Create first reminder
        reminder_service.create_individual_reminder(
            patient_id=sample_patient_medication.patient_id,
            patient_medication_id=sample_patient_medication.id,
            scheduled_time=scheduled_time
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="Reminder already exists for this medication at this time"):
            reminder_service.create_individual_reminder(
                patient_id=sample_patient_medication.patient_id,
                patient_medication_id=sample_patient_medication.id,
                scheduled_time=scheduled_time
            )


class TestReminderInstanceManagement:
    """Test reminder instance management methods"""

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

    def test_get_pending_reminders_with_patient_filter(self, reminder_service, test_db, sample_patient_medication):
        """Test getting pending reminders for specific patient"""
        # Create reminders for different patients
        reminder1 = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() - timedelta(minutes=5),
            actual_dose_time=datetime.now() - timedelta(minutes=5) + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Patient 1 reminder"
        )

        # Create another patient medication for patient 2
        med2 = PatientMedication(
            patient_id=2,
            medication_id=1,
            dosage="200mg",
            instructions="Take twice daily",
            times_per_day=2,
            start_date=datetime.now(),
            end_date=None,
            status="active",
            confirmed_by_patient=True,
            assigned_by_doctor=1  # Add missing field
        )
        test_db.add(med2)
        test_db.commit()

        reminder2 = Reminder(
            patient_medication_id=med2.id,
            patient_id=2,
            scheduled_time=datetime.now() - timedelta(minutes=5),
            actual_dose_time=datetime.now() - timedelta(minutes=5) + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Patient 2 reminder"
        )

        test_db.add(reminder1)
        test_db.add(reminder2)
        test_db.commit()

        # Get reminders for patient 1 only
        patient1_reminders = reminder_service.get_pending_reminders(patient_id=1)

        assert len(patient1_reminders) == 1
        assert patient1_reminders[0].message_text == "Patient 1 reminder"

    def test_get_patient_reminders(self, reminder_service, test_db, sample_patient_medication):
        """Test getting reminders for a patient with filters"""
        # Create reminders with different statuses
        pending_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() + timedelta(hours=1),
            actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Pending reminder"
        )

        sent_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() - timedelta(hours=1),
            actual_dose_time=datetime.now() - timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,
            message_text="Sent reminder"
        )

        test_db.add(pending_reminder)
        test_db.add(sent_reminder)
        test_db.commit()

        # Test getting all reminders
        all_reminders = reminder_service.get_patient_reminders(patient_id=1)
        assert len(all_reminders) >= 2

        # Test filtering by status
        sent_only = reminder_service.get_patient_reminders(patient_id=1, status="sent")
        assert len(sent_only) >= 1
        assert all(r.status.value == "sent" for r in sent_only)

    def test_get_reminder_by_id(self, reminder_service, test_db, sample_patient_medication):
        """Test getting specific reminder by ID"""
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

        result = reminder_service.get_reminder_by_id(
            patient_id=1,
            reminder_id=reminder.id
        )

        assert result is not None
        assert result.id == reminder.id
        assert result.message_text == "Test reminder"

    def test_get_reminder_by_id_not_found(self, reminder_service):
        """Test getting non-existent reminder"""
        result = reminder_service.get_reminder_by_id(
            patient_id=1,
            reminder_id=999
        )

        assert result is None

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
            reason="Patient requested cancellation"
        )

        assert canceled_reminder.status == ReminderStatusEnum.cancelled
        assert canceled_reminder.response_text == "Patient requested cancellation"

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

    def test_mark_reminder_sent_not_found(self, reminder_service):
        """Test marking non-existent reminder as sent"""
        with pytest.raises(ValueError, match="Reminder not found"):
            reminder_service.mark_reminder_sent(
                reminder_id=999,
                channel="whatsapp"
            )

    def test_mark_reminder_delivered(self, reminder_service, test_db, sample_patient_medication):
        """Test marking reminder as delivered"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now(),
            actual_dose_time=datetime.now() + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,
            message_text="Test reminder",
            twilio_message_sid="SM123456789"
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        delivered_reminder = reminder_service.mark_reminder_delivered("SM123456789")

        assert delivered_reminder is not None
        assert delivered_reminder.status == ReminderStatusEnum.delivered
        assert delivered_reminder.delivered_at is not None

    def test_mark_reminder_delivered_not_found(self, reminder_service):
        """Test marking non-existent message sid as delivered"""
        result = reminder_service.mark_reminder_delivered("SM999999999")
        assert result is None

    def test_mark_reminder_failed(self, reminder_service, test_db, sample_patient_medication):
        """Test marking reminder as failed"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now(),
            actual_dose_time=datetime.now() + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder",
            retry_count=0
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        failed_reminder = reminder_service.mark_reminder_failed(
            reminder_id=reminder.id,
            error_message="Network timeout"
        )

        assert failed_reminder.status == ReminderStatusEnum.failed
        assert failed_reminder.twilio_error_message == "Network timeout"
        assert failed_reminder.retry_count == 1
        assert failed_reminder.last_retry_at is not None

    def test_record_reminder_response(self, reminder_service, test_db, sample_patient_medication):
        """Test recording patient response to reminder"""
        reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now(),
            actual_dose_time=datetime.now() + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,
            message_text="Test reminder",
            twilio_message_sid="SM123456789"
        )
        test_db.add(reminder)
        test_db.commit()
        test_db.refresh(reminder)

        responded_reminder = reminder_service.record_reminder_response(
            message_sid="SM123456789",
            response_text="TAKEN"
        )

        assert responded_reminder is not None
        assert responded_reminder.status == ReminderStatusEnum.responded
        assert responded_reminder.response_text == "TAKEN"
        assert responded_reminder.response_received_at is not None


class TestReminderGeneration:
    """Test reminder generation methods"""

    def test_generate_reminders_for_schedule_inactive(self, reminder_service, test_db, sample_patient_medication):
        """Test generating reminders for inactive schedule"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=False,  # Inactive
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

        reminders = reminder_service.generate_reminders_for_schedule(schedule.id)

        assert len(reminders) == 0

    def test_generate_reminders_for_schedule_no_medication(self, reminder_service, test_db):
        """Test generating reminders when patient medication doesn't exist"""
        schedule = ReminderSchedule(
            patient_medication_id=999,  # Non-existent
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

        reminders = reminder_service.generate_reminders_for_schedule(schedule.id)

        assert len(reminders) == 0

    def test_generate_reminders_for_schedule_success(self, reminder_service, test_db, sample_patient_medication):
        """Test successfully generating reminders for schedule"""
        schedule = ReminderSchedule(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            is_active=True,
            frequency="daily",
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
            start_date=datetime.now() - timedelta(days=1),  # Start yesterday
            end_date=datetime.now() + timedelta(days=5)  # End in 5 days
        )
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        reminders = reminder_service.generate_reminders_for_schedule(schedule.id, days_ahead=3)

        # Should create reminders for today and tomorrow (past ones skipped)
        assert len(reminders) >= 4  # 2 times per day × 2 days

        for reminder in reminders:
            assert reminder.patient_medication_id == sample_patient_medication.id
            assert reminder.patient_id == 1
            assert reminder.status == ReminderStatusEnum.pending
            assert reminder.channel == ReminderChannelEnum.whatsapp
            assert "Aspirin" in reminder.message_text

    def test_generate_reminder_message(self, reminder_service, sample_patient_medication):
        """Test generating reminder message text"""
        dose_time = datetime(2025, 12, 23, 8, 0, 0)  # 8:00 AM

        message = reminder_service._generate_reminder_message(
            sample_patient_medication,
            dose_time
        )

        assert "⏰ Medication Reminder" in message
        assert "Aspirin" in message
        assert "100mg" in message
        assert "08:00 AM" in message
        assert "Reply TAKEN" in message


class TestReminderStatistics:
    """Test reminder statistics methods"""

    def test_get_reminder_stats(self, reminder_service, test_db, sample_patient_medication):
        """Test getting reminder statistics"""
        base_time = datetime.now() - timedelta(days=10)

        # Create various reminders within the last 30 days
        reminders_data = [
            (ReminderStatusEnum.sent, base_time + timedelta(days=1)),
            (ReminderStatusEnum.sent, base_time + timedelta(days=2)),
            (ReminderStatusEnum.delivered, base_time + timedelta(days=3)),
            (ReminderStatusEnum.delivered, base_time + timedelta(days=4)),
            (ReminderStatusEnum.responded, base_time + timedelta(days=5)),
            (ReminderStatusEnum.responded, base_time + timedelta(days=6)),
            (ReminderStatusEnum.failed, base_time + timedelta(days=7)),
            (ReminderStatusEnum.pending, base_time + timedelta(days=8)),
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

        # Create old reminder (outside 30-day window)
        old_reminder = Reminder(
            patient_medication_id=sample_patient_medication.id,
            patient_id=1,
            scheduled_time=datetime.now() - timedelta(days=40),
            actual_dose_time=datetime.now() - timedelta(days=40) + timedelta(minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.sent,
            message_text="Old reminder"
        )
        test_db.add(old_reminder)

        test_db.commit()

        stats = reminder_service.get_reminder_stats(patient_id=1, days=30)

        assert stats["total_scheduled"] == 8  # Excludes old reminder
        assert stats["sent"] == 6  # sent + delivered + responded
        assert stats["delivered"] == 4  # delivered + responded
        assert stats["responded"] == 2
        assert stats["failed"] == 1
        assert stats["delivery_rate"] == 50.0  # 4/8 * 100
        assert stats["response_rate"] == 50.0  # 2/4 * 100

    def test_get_reminder_stats_no_reminders(self, reminder_service):
        """Test getting statistics when no reminders exist"""
        stats = reminder_service.get_reminder_stats(patient_id=1, days=30)

        assert stats["total_scheduled"] == 0
        assert stats["sent"] == 0
        assert stats["delivered"] == 0
        assert stats["responded"] == 0
        assert stats["failed"] == 0
        assert stats["delivery_rate"] == 0
        assert stats["response_rate"] == 0