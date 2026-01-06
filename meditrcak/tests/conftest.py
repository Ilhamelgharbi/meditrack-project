"""
Pytest configuration and shared fixtures for MediTrack AI tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base, get_db
from main import app
from app.auth.models import User
from app.patients.models import Patient
from app.medications.models import Medication, PatientMedication
from app.reminders.models import Reminder, ReminderStatusEnum, ReminderChannelEnum
from app.auth.utils import hash_password


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    # Ensure tables are created
    Base.metadata.create_all(bind=test_engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()

    # Clean up any existing data - handle potential foreign key issues
    try:
        # Try to delete in reverse dependency order
        db.execute("DELETE FROM medication_logs")
        db.execute("DELETE FROM reminders")
        db.execute("DELETE FROM reminder_schedules")
        db.execute("DELETE FROM patient_medications")
        db.execute("DELETE FROM medications")
        db.execute("DELETE FROM patients")
        db.execute("DELETE FROM users")
        db.commit()
    except Exception:
        # If deletion fails, rollback and continue
        db.rollback()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(test_db):
    """Create FastAPI test client"""
    # Create a test app without lifespan events
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    test_app = FastAPI(title="Test MediTrack AI")
    
    # Add CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from app.auth.routes import router as auth_router
    from app.patients.routes import router as patients_router
    from app.medications.routes import router as medications_router
    from app.adherence.routes import router as adherence_router
    from app.reminders.routes import router as reminders_router
    from app.analytics import router as analytics_router
    from app.agent.router import router as agent_router
    from app.agent.utils.text_to_speech import router as tts_router
    
    test_app.include_router(auth_router)
    test_app.include_router(patients_router)
    test_app.include_router(medications_router)
    test_app.include_router(adherence_router)
    test_app.include_router(reminders_router)
    test_app.include_router(analytics_router)
    test_app.include_router(agent_router)
    test_app.include_router(tts_router)
    
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        full_name="Test User",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role="patient",
        phone="+1234567890"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_admin(test_db):
    """Create test admin user"""
    admin = User(
        full_name="Test Admin",
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        role="admin",
        phone="+1234567891"
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest.fixture
def test_patient(test_db, test_user):
    """Create test patient profile"""
    patient = Patient(
        user_id=test_user.id,
        date_of_birth="1990-01-01",
        gender="male",
        medical_conditions="None",
        allergies="None",
        emergency_contact_name="Emergency Contact",
        emergency_contact_phone="+1234567892"
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture
def test_medication(test_db):
    """Create test medication"""
    medication = Medication(
        name="Test Medication",
        generic_name="Test Generic",
        dosage_form="tablet",
        strength="10mg",
        description="Test medication for testing"
    )
    test_db.add(medication)
    test_db.commit()
    test_db.refresh(medication)
    return medication


@pytest.fixture
def test_patient_medication(test_db, test_user, test_medication):
    """Create test patient medication assignment"""
    patient_medication = PatientMedication(
        patient_id=test_user.id,
        medication_id=test_medication.id,
        prescribed_dosage="10mg",
        frequency="once daily",
        instructions="Take with food",
        prescribed_by="Dr. Test",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    test_db.add(patient_medication)
    test_db.commit()
    test_db.refresh(patient_medication)
    return patient_medication


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post("/auth/login", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, test_admin):
    """Get authentication headers for test admin"""
    response = client.post("/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_reminder(test_db, test_user, test_patient_medication):
    """Create test reminder"""
    from datetime import datetime, timedelta
    
    reminder = Reminder(
        patient_medication_id=test_patient_medication.id,
        patient_id=test_user.id,
        scheduled_time=datetime.now() + timedelta(hours=1),
        actual_dose_time=datetime.now() + timedelta(hours=1, minutes=15),
        reminder_advance_minutes=15,
        channel=ReminderChannelEnum.whatsapp,
        status=ReminderStatusEnum.pending,
        message_text="Test reminder message"
    )
    test_db.add(reminder)
    test_db.commit()
    test_db.refresh(reminder)
    return reminder


@pytest.fixture(autouse=True)
def setup_test_data(test_db):
    """Set up any common test data"""
    # This can be extended to create common test data
    pass