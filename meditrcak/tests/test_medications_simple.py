"""
Simplified medication tests - Basic functionality tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from main import app
from app.database.db import get_db
from app.auth.models import Base

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
admin_reg_data = {
    "full_name": "Med Admin",
    "email": "med.admin@test.com",
    "phone": "+1111111111",
    "password": "admin123",
    "role": "admin"
}

patient_reg_data = {
    "full_name": "Med Patient",
    "email": "med.patient@test.com",
    "phone": "+2222222222",
    "password": "patient123",
    "role": "patient"
}


def get_admin_token():
    """Register and login as admin"""
    # Register
    client.post("/auth/register", json=admin_reg_data)
    # Login with form data (OAuth2PasswordRequestForm uses username field)
    response = client.post("/auth/login", data={
        "username": admin_reg_data["email"],
        "password": admin_reg_data["password"]
    })
    return response.json()["access_token"]


def get_patient_token():
    """Register and login as patient"""
    # Register
    client.post("/auth/register", json=patient_reg_data)
    # Login with form data (OAuth2PasswordRequestForm uses username field)
    response = client.post("/auth/login", data={
        "username": patient_reg_data["email"],
        "password": patient_reg_data["password"]
    })
    return response.json()["access_token"]


# ==================== MEDICATION CATALOG TESTS ====================

def test_create_medication_as_admin():
    """Test admin can create medication in catalog"""
    token = get_admin_token()
    
    response = client.post(
        "/medications/",
        json={
            "name": "Paracetamol",
            "form": "tablet",
            "default_dosage": "500mg",
            "side_effects": "Rare allergic reactions",
            "warnings": "Do not exceed 4g per day"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Paracetamol"
    assert data["form"] == "tablet"
    assert "id" in data


def test_create_medication_as_patient_fails():
    """Test patient cannot create medication"""
    token = get_patient_token()
    
    response = client.post(
        "/medications/",
        json={
            "name": "Ibuprofen",
            "form": "tablet",
            "default_dosage": "400mg"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403


def test_get_all_medications():
    """Test getting all medications from catalog"""
    admin_token = get_admin_token()
    
    # Create a medication first
    client.post(
        "/medications/",
        json={
            "name": "Aspirin",
            "form": "tablet",
            "default_dosage": "100mg"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Get all medications
    response = client.get(
        "/medications/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(med["name"] == "Aspirin" for med in data)


def test_medication_workflow():
    """Test complete workflow: create → assign → confirm → stop"""
    admin_token = get_admin_token()
    patient_token = get_patient_token()
    
    # Get patient ID
    patient_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    patient_id = patient_response.json()["id"]
    
    # 1. Admin creates medication
    med_response = client.post(
        "/medications/",
        json={
            "name": "Workflow Test Med",
            "form": "tablet",
            "default_dosage": "50mg"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert med_response.status_code == 201
    medication_id = med_response.json()["id"]
    
    # 2. Admin assigns to patient
    assign_response = client.post(
        f"/medications/patients/{patient_id}/medications",
        json={
            "medication_id": medication_id,
            "dosage": "50mg",
            "instructions": "Take as needed",
            "times_per_day": 1,
            "start_date": str(date.today())
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]
    assert assign_response.json()["status"] == "pending"
    
    # 3. Patient confirms medication
    confirm_response = client.patch(
        f"/medications/patients/{patient_id}/medications/{assignment_id}/confirm",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "active"
    
    # 4. Admin stops medication
    stop_response = client.patch(
        f"/medications/patients/{patient_id}/medications/{assignment_id}/stop",
        json={"reason": "Treatment completed"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stop_response.status_code == 200
    assert stop_response.json()["reason"] == "Treatment completed"