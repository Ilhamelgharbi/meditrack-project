"""
Unit tests for reminder API routes
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base, get_db
from main import app
from app.auth.models import User
from app.patients.models import Patient
from app.medications.models import PatientMedication, Medication, MedicationStatusEnum
from app.reminders.models import ReminderSchedule
from app.auth.services import get_current_user
from app.auth.utils import hash_password


@pytest.fixture
def test_db():
    """Create in-memory test database"""
    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up the test database file
        import os
        if os.path.exists("test.db"):
            os.remove("test.db")


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        full_name="Test User",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role="patient"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def client(test_db, test_user):
    """Create test client with database and auth dependency overrides"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here to avoid threading issues

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    return client


@pytest.fixture
def unauthorized_client(test_db):
    """Create test client with database override but no auth override"""
    from fastapi import HTTPException, status
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here to avoid threading issues

    def override_get_current_user():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    return client


@pytest.fixture
def test_patient(test_db, test_user):
    """Create test patient profile"""
    patient = Patient(
        user_id=test_user.id,
        date_of_birth=datetime(1990, 1, 1),
        gender="male",
        status="stable"
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture
def test_medication(test_db, test_user):
    """Create test medication"""
    medication = Medication(
        name="Aspirin",
        form="tablet",
        default_dosage="100mg",
        created_by=test_user.id
    )
    test_db.add(medication)
    test_db.commit()
    test_db.refresh(medication)
    return medication


@pytest.fixture
def test_patient_medication(test_db, test_patient, test_medication, test_user):
    """Create test patient medication"""
    patient_med = PatientMedication(
        patient_id=test_patient.id,
        medication_id=test_medication.id,
        dosage="100mg",
        instructions="Take once daily",
        times_per_day=1,
        start_date=datetime.now(),
        end_date=None,
        status="active",
        confirmed_by_patient=True,
        assigned_by_doctor=test_user.id
    )
    test_db.add(patient_med)
    test_db.commit()
    test_db.refresh(patient_med)
    return patient_med


@pytest.fixture
def auth_headers():
    """Mock authentication headers since we're overriding get_current_user"""
    return {"Authorization": "Bearer mock_token"}


class TestReminderScheduleRoutes:
    """Test reminder schedule API routes"""

    def test_create_reminder_schedule_success(self, client, auth_headers, test_patient_medication):
        """Test creating reminder schedule successfully"""
        schedule_data = {
            "patient_medication_id": test_patient_medication.id,
            "frequency": "daily",
            "reminder_times": ["08:00", "20:00"],
            "advance_minutes": 15,
            "channel_whatsapp": True,
            "channel_sms": False,
            "channel_push": True,
            "channel_email": False,
            "auto_skip_if_taken": True,
            "escalate_if_missed": True,
            "escalate_delay_minutes": 30,
            "quiet_hours_enabled": False,
            "start_date": datetime.now().isoformat(),
            "end_date": None
        }

        response = client.post("/reminders/schedules", json=schedule_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["patient_medication_id"] == test_patient_medication.id
        assert data["frequency"] == "daily"
        assert data["advance_minutes"] == 15
        assert data["channel_whatsapp"] == True

    def test_create_reminder_schedule_unauthorized(self, unauthorized_client, test_patient_medication):
        """Test creating schedule without authentication"""
        schedule_data = {
            "patient_medication_id": test_patient_medication.id,
            "frequency": "daily",
            "reminder_times": ["08:00"],
            "advance_minutes": 15,
            "channel_whatsapp": True,
            "channel_sms": False,
            "channel_push": True,
            "channel_email": False,
            "auto_skip_if_taken": True,
            "escalate_if_missed": True,
            "escalate_delay_minutes": 30,
            "quiet_hours_enabled": False,
            "start_date": datetime.now().isoformat(),
            "end_date": None
        }

        response = unauthorized_client.post("/reminders/schedules", json=schedule_data)

        assert response.status_code == 401

    def test_get_reminder_schedules(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting reminder schedules"""
        # Create a schedule first
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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
            start_date=datetime.now(),
            end_date=None
        )
        test_db.add(schedule)
        test_db.commit()

        response = client.get("/reminders/schedules", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["frequency"] == "daily"
        assert data[0]["advance_minutes"] == 15

    def test_get_reminder_schedules_active_only(self, client, auth_headers, test_patient_medication, test_db, test_patient, test_medication, test_user):
        """Test getting only active reminder schedules"""
        # Create another patient medication for the inactive schedule
        inactive_patient_medication = PatientMedication(
            patient_id=test_patient.id,
            medication_id=test_medication.id,
            dosage="10mg",
            instructions="Take with food",
            times_per_day=2,
            start_date=datetime.now().date(),
            end_date=None,
            status=MedicationStatusEnum.active,
            confirmed_by_patient=True,
            assigned_by_doctor=test_user.id
        )
        test_db.add(inactive_patient_medication)
        test_db.commit()
        test_db.refresh(inactive_patient_medication)
        
        # Create active schedule
        active_schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        # Create inactive schedule
        inactive_schedule = ReminderSchedule(
            patient_medication_id=inactive_patient_medication.id,
            patient_id=inactive_patient_medication.patient_id,
            is_active=False,
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

        test_db.add(active_schedule)
        test_db.add(inactive_schedule)
        test_db.commit()

        response = client.get("/reminders/schedules?active_only=true", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] == True

    def test_get_reminder_schedule_by_medication(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting reminder schedule by medication ID"""
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        response = client.get(f"/reminders/schedules/medication/{test_patient_medication.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["patient_medication_id"] == test_patient_medication.id
        assert data["frequency"] == "daily"

    def test_get_reminder_schedule_by_medication_not_found(self, client, auth_headers):
        """Test getting reminder schedule for non-existent medication"""
        response = client.get("/reminders/schedules/medication/999", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_reminder_schedule(self, client, auth_headers, test_patient_medication, test_db):
        """Test updating reminder schedule"""
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        update_data = {
            "advance_minutes": 30,
            "channel_sms": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }

        response = client.put(f"/reminders/schedules/{schedule.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["advance_minutes"] == 30
        assert data["channel_sms"] == True
        assert data["quiet_hours_enabled"] == True

    def test_delete_reminder_schedule(self, client, auth_headers, test_patient_medication, test_db):
        """Test deleting reminder schedule"""
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        response = client.delete(f"/reminders/schedules/{schedule.id}", headers=auth_headers)

        assert response.status_code == 204

    def test_toggle_reminder_schedule(self, client, auth_headers, test_patient_medication, test_db):
        """Test toggling reminder schedule active status"""
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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
        response = client.post(f"/reminders/schedules/{schedule.id}/toggle?is_active=false", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        assert "disabled" in data["message"]


class TestReminderRoutes:
    """Test individual reminder API routes"""

    def test_get_reminders(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting reminders"""
        from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum

        reminder = Reminder(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Test reminder"
        )
        test_db.add(reminder)
        test_db.commit()

        response = client.get("/reminders/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Find our test reminder
        test_reminder = next((r for r in data if r["message_text"] == "Test reminder"), None)
        assert test_reminder is not None
        assert test_reminder["status"] == "pending"

    def test_get_reminders_with_filters(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting reminders with status filter"""
        from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum

        # Create reminders with different statuses
        pending_reminder = Reminder(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
            reminder_advance_minutes=15,
            channel=ReminderChannelEnum.whatsapp,
            status=ReminderStatusEnum.pending,
            message_text="Pending reminder"
        )

        sent_reminder = Reminder(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        # Filter by pending status
        response = client.get("/reminders/?status=pending", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(r["status"] == "pending" for r in data)

    def test_get_reminder_by_id(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting specific reminder by ID"""
        from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum

        reminder = Reminder(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        response = client.get(f"/reminders/{reminder.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == reminder.id
        assert data["message_text"] == "Test reminder"
        assert data["status"] == "pending"

    def test_cancel_reminder(self, client, auth_headers, test_patient_medication, test_db):
        """Test canceling a pending reminder"""
        from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum

        reminder = Reminder(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        cancel_data = {"reason": "Patient requested cancellation"}

        response = client.post(f"/reminders/{reminder.id}/cancel", json=cancel_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["response_text"] == "Patient requested cancellation"

    def test_get_reminder_stats(self, client, auth_headers, test_patient_medication, test_db):
        """Test getting reminder statistics"""
        from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum

        # Create some test reminders
        reminders_data = [
            ReminderStatusEnum.sent,
            ReminderStatusEnum.sent,
            ReminderStatusEnum.delivered,
            ReminderStatusEnum.responded,
            ReminderStatusEnum.failed,
        ]

        for i, status in enumerate(reminders_data):
            reminder = Reminder(
                patient_medication_id=test_patient_medication.id,
                patient_id=test_patient_medication.patient_id,
                scheduled_time=datetime.now() - timedelta(days=i),
                actual_dose_time=datetime.now() - timedelta(days=i, minutes=15),
                reminder_advance_minutes=15,
                channel=ReminderChannelEnum.whatsapp,
                status=status,
                message_text=f"Test reminder {i}"
            )
            test_db.add(reminder)

        test_db.commit()

        response = client.get("/reminders/stats/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_scheduled" in data
        assert "sent" in data
        assert "delivered" in data
        assert "responded" in data
        assert "failed" in data
        assert data["total_scheduled"] >= 5


class TestReminderGenerationRoutes:
    """Test reminder generation API routes"""

    def test_generate_reminders_for_schedule(self, client, auth_headers, test_patient_medication, test_db):
        """Test generating reminders for a schedule"""
        # Create a schedule first
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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
            start_date=datetime.now(),
            end_date=None
        )
        test_db.add(schedule)
        test_db.commit()
        test_db.refresh(schedule)

        # Generate reminders for the next 3 days
        generate_data = {
            "days_ahead": 3
        }

        response = client.post(f"/reminders/schedules/{schedule.id}/generate", json=generate_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "message" in data
        assert "reminders" in data
        assert data["count"] >= 6  # 2 reminders per day for 3 days

    def test_generate_reminders_unauthorized(self, unauthorized_client, test_patient_medication, test_db):
        """Test generating reminders without authentication"""
        # Create a schedule first
        schedule = ReminderSchedule(
            patient_medication_id=test_patient_medication.id,
            patient_id=test_patient_medication.patient_id,
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

        generate_data = {
            "days_ahead": 1
        }

        response = unauthorized_client.post(f"/reminders/schedules/{schedule.id}/generate", json=generate_data)

        assert response.status_code == 401

    def test_generate_reminders_schedule_not_found(self, client, auth_headers):
        """Test generating reminders for non-existent schedule"""
        generate_data = {
            "days_ahead": 1
        }

        response = client.post("/reminders/schedules/999/generate", json=generate_data, headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()