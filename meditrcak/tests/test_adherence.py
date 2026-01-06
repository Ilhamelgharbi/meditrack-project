"""
Unit tests for adherence tracking
Tests for medication logging, adherence stats, and goal tracking
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, date, timedelta

from main import app
from app.database.db import get_db
from app.auth.models import Base, User, RoleEnum
from app.medications.models import Medication, PatientMedication, MedicationFormEnum, MedicationStatusEnum
from app.adherence.models import MedicationLog, AdherenceStats, MedicationLogStatusEnum
from app.auth.utils import hash_password


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Test data
admin_data = {
    "full_name": "Dr. Adherence Test",
    "email": "adherence.admin@test.com",
    "phone": "+1111111111",
    "password": "admin123",
    "role": "admin"
}

patient_data = {
    "full_name": "Patient Adherence Test",
    "email": "adherence.patient@test.com",
    "phone": "+2222222222",
    "password": "patient123",
    "role": "patient"
}


def get_admin_token():
    """Register and login as admin"""
    client.post("/auth/register", json=admin_data)
    response = client.post("/auth/login", data={
        "username": admin_data["email"],
        "password": admin_data["password"]
    })
    return response.json()["access_token"]


def get_patient_token():
    """Register and login as patient"""
    client.post("/auth/register", json=patient_data)
    response = client.post("/auth/login", data={
        "username": patient_data["email"],
        "password": patient_data["password"]
    })
    return response.json()["access_token"]


def setup_patient_medication(admin_token, patient_token):
    """Helper to create medication and assign to patient"""
    # Get patient ID
    patient_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    patient_id = patient_response.json()["id"]
    
    # Create medication
    med_response = client.post(
        "/medications/",
        json={
            "name": "Test Medication",
            "form": "tablet",
            "default_dosage": "500mg"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    medication_id = med_response.json()["id"]
    
    # Assign to patient
    assign_response = client.post(
        f"/medications/patients/{patient_id}/medications",
        json={
            "medication_id": medication_id,
            "dosage": "500mg",
            "instructions": "Take once daily",
            "times_per_day": 1,
            "start_date": str(date.today())
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Confirm medication
    assignment_id = assign_response.json()["id"]
    client.patch(
        f"/medications/patients/{patient_id}/medications/{assignment_id}/confirm",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    return patient_id, assignment_id


# ==================== MEDICATION LOG TESTS ====================

def test_log_medication_taken():
    """Test logging a taken medication dose"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    actual_time = datetime.now().replace(hour=8, minute=5, second=0, microsecond=0)
    
    response = client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "taken",
            "actual_time": actual_time.isoformat(),
            "notes": "Took with breakfast",
            "logged_via": "manual"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "taken"
    assert data["patient_medication_id"] == assignment_id
    assert data["on_time"] == True  # Within 30 minutes
    assert data["minutes_late"] == 5
    assert data["notes"] == "Took with breakfast"


def test_log_medication_skipped():
    """Test logging a skipped medication dose"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    response = client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "skipped",
            "skipped_reason": "Felt nauseous",
            "logged_via": "manual"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "skipped"
    assert data["skipped_reason"] == "Felt nauseous"
    assert data["actual_time"] is None


def test_log_medication_missed():
    """Test logging a missed medication dose"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now() - timedelta(hours=2)
    
    response = client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "missed",
            "logged_via": "auto"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "missed"
    assert data["logged_via"] == "auto"


def test_log_medication_late():
    """Test logging medication taken late (>30 minutes)"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    actual_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # 1 hour late
    
    response = client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "taken",
            "actual_time": actual_time.isoformat()
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "taken"
    assert data["on_time"] == False  # More than 30 minutes late
    assert data["minutes_late"] == 60


def test_duplicate_log_fails():
    """Test that duplicate logs for same scheduled time are rejected"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    log_data = {
        "patient_medication_id": assignment_id,
        "scheduled_time": scheduled_time.isoformat(),
        "status": "taken",
        "actual_time": scheduled_time.isoformat()
    }
    
    # First log should succeed
    response1 = client.post(
        "/adherence/logs",
        json=log_data,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response1.status_code == 201
    
    # Second log should fail
    response2 = client.post(
        "/adherence/logs",
        json=log_data,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


def test_update_medication_log():
    """Test updating an existing medication log"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    scheduled_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Create log
    create_response = client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "skipped",
            "skipped_reason": "Forgot"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    log_id = create_response.json()["id"]
    
    # Update to taken
    update_response = client.put(
        f"/adherence/logs/{log_id}",
        json={
            "status": "taken",
            "actual_time": scheduled_time.isoformat(),
            "notes": "Actually took it later"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "taken"
    assert data["notes"] == "Actually took it later"


def test_get_medication_logs():
    """Test retrieving medication logs with filters"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    # Create multiple logs
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    for i in range(5):
        log_time = today - timedelta(days=i)
        status = "taken" if i % 2 == 0 else "skipped"
        
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": status,
                "actual_time": log_time.isoformat() if status == "taken" else None
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get all logs
    response = client.get(
        "/adherence/logs",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Filter by status
    response_taken = client.get(
        "/adherence/logs?status=taken",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response_taken.status_code == 200
    taken_logs = response_taken.json()
    assert len(taken_logs) == 3
    assert all(log["status"] == "taken" for log in taken_logs)


# ==================== ADHERENCE STATS TESTS ====================

def test_calculate_adherence_score():
    """Test adherence score calculation"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    # Create logs: 7 taken, 2 skipped, 1 missed (70% adherence)
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    statuses = ["taken"] * 7 + ["skipped"] * 2 + ["missed"] * 1
    
    for i, status in enumerate(statuses):
        log_time = today - timedelta(days=i)
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": status,
                "actual_time": log_time.isoformat() if status == "taken" else None
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get weekly stats (last 7 days + today = 8 days)
    response = client.get(
        "/adherence/stats?period=weekly",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_scheduled"] == 8  # Weekly = today + 7 days = 8 logs
    assert stats["total_taken"] == 7  # All 7 "taken" logs are within 8 days
    assert stats["total_skipped"] == 1  # Only 1 skipped within 8 days
    assert stats["total_missed"] == 0  # The missed log (day 9) is outside weekly range
    assert stats["adherence_score"] == 87.5  # 7/8 = 87.5%


def test_streak_calculation():
    """Test current and longest streak calculation"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    # Create perfect streak for last 5 days
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    for i in range(5):
        log_time = today - timedelta(days=i)
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": "taken",
                "actual_time": log_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get stats
    response = client.get(
        "/adherence/stats?period=weekly",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    stats = response.json()
    assert stats["current_streak"] == 5
    assert stats["longest_streak"] == 5


def test_broken_streak():
    """Test that missed dose breaks streak"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Perfect streak for 3 days
    for i in range(3):
        log_time = today - timedelta(days=i)
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": "taken",
                "actual_time": log_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Missed dose breaks streak
    missed_time = today - timedelta(days=3)
    client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment_id,
            "scheduled_time": missed_time.isoformat(),
            "status": "missed"
        },
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    # Get stats
    response = client.get(
        "/adherence/stats?period=weekly",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    stats = response.json()
    assert stats["current_streak"] == 3  # Only counts from today backwards
    assert stats["longest_streak"] == 3


def test_get_chart_data():
    """Test adherence chart data generation"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    # Create varied logs over 7 days
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    for i in range(7):
        log_time = today - timedelta(days=i)
        # Alternate between 100% and 0% adherence
        status = "taken" if i % 2 == 0 else "missed"
        
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": status,
                "actual_time": log_time.isoformat() if status == "taken" else None
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get chart data
    response = client.get(
        "/adherence/chart?days=7",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    chart_data = response.json()
    assert len(chart_data) == 7  # 7 days of data
    
    # Verify data structure
    for day_data in chart_data:
        assert "date" in day_data
        assert "score" in day_data
        assert "taken" in day_data
        assert "scheduled" in day_data
        assert "status" in day_data
        assert day_data["status"] in ["excellent", "good", "fair", "poor"]


def test_get_adherence_dashboard():
    """Test complete adherence dashboard"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    # Create some logs
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    for i in range(10):
        log_time = today - timedelta(days=i)
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": "taken",
                "actual_time": log_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get dashboard
    response = client.get(
        "/adherence/dashboard",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    dashboard = response.json()
    
    assert "overall_stats" in dashboard
    assert "weekly_stats" in dashboard
    assert "daily_stats" in dashboard
    assert "chart_data" in dashboard
    assert "recent_logs" in dashboard
    
    assert dashboard["overall_stats"]["adherence_score"] == 100.0


def test_patient_cannot_view_other_patient_logs():
    """Test that patients can only view their own logs"""
    admin_token = get_admin_token()
    patient1_token = get_patient_token()
    
    # Create second patient
    patient2_data = {
        "full_name": "Patient Two",
        "email": "patient2@test.com",
        "phone": "+3333333333",
        "password": "patient123",
        "role": "patient"
    }
    client.post("/auth/register", json=patient2_data)
    patient2_response = client.post("/auth/login", data={
        "username": patient2_data["email"],
        "password": patient2_data["password"]
    })
    patient2_token = patient2_response.json()["access_token"]
    
    # Setup medication for patient 1
    patient1_id, assignment1_id = setup_patient_medication(admin_token, patient1_token)
    
    # Create log for patient 1
    scheduled_time = datetime.now()
    client.post(
        "/adherence/logs",
        json={
            "patient_medication_id": assignment1_id,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "taken",
            "actual_time": scheduled_time.isoformat()
        },
        headers={"Authorization": f"Bearer {patient1_token}"}
    )
    
    # Patient 2 tries to view patient 1's logs
    response = client.get(
        "/adherence/logs",
        headers={"Authorization": f"Bearer {patient2_token}"}
    )
    
    # Should return empty list (no logs for patient 2)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_on_time_score_calculation():
    """Test on-time score calculation"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    patient_id, assignment_id = setup_patient_medication(admin_token, patient_token)
    
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    # 3 on-time, 2 late
    for i in range(5):
        log_time = today - timedelta(days=i)
        actual_time = log_time + timedelta(minutes=10 if i < 3 else 60)  # First 3 on time
        
        client.post(
            "/adherence/logs",
            json={
                "patient_medication_id": assignment_id,
                "scheduled_time": log_time.isoformat(),
                "status": "taken",
                "actual_time": actual_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
    
    # Get stats
    response = client.get(
        "/adherence/stats?period=weekly",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_taken"] == 5
    assert stats["on_time_score"] == 60.0  # 3 out of 5 on time