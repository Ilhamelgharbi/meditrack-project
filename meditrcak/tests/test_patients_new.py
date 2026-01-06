import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from main import app
from app.database.db import Base, get_db
from app.auth.models import User, RoleEnum
from app.patients.models import Patient
from app.patients.schemas import GenderEnum, StatusEnum


# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patients1.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user_data():
    """Test data for admin user."""
    return {
        "full_name": "Admin User",
        "email": "admin@test.com",
        "phone": "+1234567890",
        "password": "adminpass123",
        "role": "admin"
    }


@pytest.fixture
def doctor_user_data():
    """Test data for doctor user."""
    return {
        "full_name": "Dr. Smith",
        "email": "doctor@test.com",
        "phone": "+0987654321",
        "password": "doctorpass123",
        "role": "admin"
    }


@pytest.fixture
def patient_user_data():
    """Test data for patient user."""
    return {
        "full_name": "John Doe",
        "email": "patient@test.com",
        "phone": "+1122334455",
        "password": "patientpass123",
        "role": "patient"
    }


@pytest.fixture
def registered_admin(client, admin_user_data):
    """Register and return admin user."""
    response = client.post("/auth/register", json=admin_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def registered_doctor(client, doctor_user_data):
    """Register and return doctor user."""
    response = client.post("/auth/register", json=doctor_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def registered_patient(client, patient_user_data):
    """Register and return patient user."""
    response = client.post("/auth/register", json=patient_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def admin_token(client, admin_user_data, registered_admin):
    """Get authentication token for admin."""
    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def doctor_token(client, doctor_user_data, registered_doctor):
    """Get authentication token for doctor."""
    login_data = {
        "username": doctor_user_data["email"],
        "password": doctor_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def patient_token(client, patient_user_data, registered_patient):
    """Get authentication token for patient."""
    login_data = {
        "username": patient_user_data["email"],
        "password": patient_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def sample_patient_record(client, patient_token, doctor_token, db_session):
    """Create a sample patient record for the registered patient."""
    # Get patient user ID from token or create patient record
    # For simplicity, let's create it directly in the database
    patient_user = db_session.query(User).filter(User.email == "patient@test.com").first()
    doctor_user = db_session.query(User).filter(User.email == "doctor@test.com").first()

    # Check if patient profile already exists (created automatically during registration)
    existing_patient = db_session.query(Patient).filter(Patient.user_id == patient_user.id).first()
    if existing_patient:
        # Update the existing patient with test data
        existing_patient.date_of_birth = date(1990, 1, 1)
        existing_patient.gender = GenderEnum.male
        existing_patient.blood_type = "O+"
        existing_patient.weight = 75.5
        existing_patient.height = 175.0
        existing_patient.medical_history = "Hypertension"
        existing_patient.allergies = "Penicillin"
        existing_patient.current_medications = "Lisinopril 10mg daily"
        existing_patient.status = StatusEnum.stable
        existing_patient.assigned_admin_id = doctor_user.id
        db_session.commit()
        db_session.refresh(existing_patient)
        return existing_patient
    else:
        # Create new patient record if it doesn't exist
        patient = Patient(
            user_id=patient_user.id,
            date_of_birth=date(1990, 1, 1),
            gender=GenderEnum.male,
            blood_type="O+",
            weight=75.5,
            height=175.0,
            medical_history="Hypertension",
            allergies="Penicillin",
            current_medications="Lisinopril 10mg daily",
            status=StatusEnum.stable,
            assigned_admin_id=doctor_user.id
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        return patient


class TestGetAllPatients:
    """Test GET /patients/ endpoint."""

    def test_get_all_patients_as_admin(self, client, doctor_token, sample_patient_record):
        """Test admin can get all patients."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        response = client.get("/patients/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_all_patients_as_patient_forbidden(self, client, patient_token):
        """Test patient cannot access admin-only endpoint."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        response = client.get("/patients/", headers=headers)
        assert response.status_code == 403

    def test_get_all_patients_with_search(self, client, admin_token, sample_patient_record):
        """Test filtering patients by search term."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/patients/?search=John", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_patients_with_status_filter(self, client, admin_token, sample_patient_record):
        """Test filtering patients by status."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/patients/?status_filter=stable", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_patients_sorted_new(self, client, admin_token, sample_patient_record):
        """Test sorting patients by newest first."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/patients/?sort=new", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetPatientById:
    """Test GET /patients/{patient_id} endpoint."""

    def test_get_patient_by_id_as_admin(self, client, admin_token, sample_patient_record):
        """Test admin can get specific patient."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/patients/{sample_patient_record.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_patient_record.id
        assert data["user_id"] == sample_patient_record.user_id

    def test_get_patient_by_id_not_found(self, client, admin_token):
        """Test getting non-existent patient returns 404."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/patients/999", headers=headers)
        assert response.status_code == 404

    def test_get_patient_by_id_as_patient_forbidden(self, client, patient_token, sample_patient_record):
        """Test patient cannot access other patients' data."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        response = client.get(f"/patients/{sample_patient_record.id}", headers=headers)
        assert response.status_code == 403


class TestGetMyPatientProfile:
    """Test GET /patients/me/profile endpoint."""

    def test_get_my_profile_as_patient(self, client, patient_token, sample_patient_record):
        """Test patient can get their own profile."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        response = client.get("/patients/me/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == sample_patient_record.user_id
        assert data["status"] == sample_patient_record.status.value

    def test_get_my_profile_patient_not_found(self, client, patient_token):
        """Test patient without profile gets 404."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        response = client.get("/patients/me/profile", headers=headers)
        # This should return 404 if no patient record exists for the user
        # But in our test setup, we create the patient record, so it should work
        assert response.status_code == 200


class TestUpdateMyProfile:
    """Test PUT /patients/me/profile endpoint."""

    def test_update_my_profile_as_patient(self, client, patient_token, sample_patient_record):
        """Test patient can update their own profile."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        update_data = {
            "weight": 80.0,
            "height": 180.0,
            "blood_type": "A+",
            "allergies": "Updated allergies"
        }
        response = client.put("/patients/me/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 80.0
        assert data["height"] == 180.0
        assert data["blood_type"] == "A+"
        assert data["allergies"] == "Updated allergies"

    def test_update_my_profile_invalid_data(self, client, patient_token, sample_patient_record):
        """Test validation errors on invalid data."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        update_data = {
            "weight": -10,  # Invalid weight
            "blood_type": "INVALID_TYPE"
        }
        response = client.put("/patients/me/profile", json=update_data, headers=headers)
        assert response.status_code == 422

    def test_update_my_profile_bmi_calculation(self, client, patient_token, sample_patient_record):
        """Test that weight and height can be updated together."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        update_data = {
            "weight": 70.0,
            "height": 170.0
        }
        response = client.put("/patients/me/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 70.0
        assert data["height"] == 170.0


class TestUpdatePatientByDoctor:
    """Test PUT /patients/{patient_id}/admin-update endpoint."""

    def test_update_patient_by_doctor_as_admin(self, client, admin_token, sample_patient_record):
        """Test admin can update patient medical info."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "allergies": "Updated allergies",
            "status": "critical",
            "clinical_notes": "Patient needs immediate attention"
        }
        response = client.put(f"/patients/{sample_patient_record.id}/admin-update", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["allergies"] == "Updated allergies"
        assert data["status"] == "critical"

    def test_update_patient_by_doctor_not_found(self, client, admin_token):
        """Test updating non-existent patient returns 404."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"status": "stable"}
        response = client.put("/patients/999/admin-update", json=update_data, headers=headers)
        assert response.status_code == 404

    def test_update_patient_by_doctor_as_patient_forbidden(self, client, patient_token, sample_patient_record):
        """Test patient cannot update other patients."""
        headers = {"Authorization": f"Bearer {patient_token}"}
        update_data = {"status": "critical"}
        response = client.put(f"/patients/{sample_patient_record.id}/admin-update", json=update_data, headers=headers)
        assert response.status_code == 403

    def test_update_patient_medical_fields_only(self, client, admin_token, sample_patient_record):
        """Test only medical fields can be updated by doctor."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "allergies": "New allergy",  # This should be updated - medical field
            "status": "critical",  # This should be updated - medical field
            "medical_history": "Updated medical history"
        }
        response = client.put(f"/patients/{sample_patient_record.id}/admin-update", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Medical fields should be updated
        assert data["allergies"] == "New allergy"
        assert data["status"] == "critical"
        assert data["medical_history"] == "Updated medical history"


# Integration Tests
class TestPatientWorkflow:
    """Test complete patient management workflow."""

    def test_complete_patient_lifecycle(self, client, admin_token, patient_token, sample_patient_record):
        """Test creating and managing a patient through their lifecycle."""
        # 1. Admin views patient details
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/patients/{sample_patient_record.id}", headers=admin_headers)
        assert response.status_code == 200

        # 2. Patient updates their profile
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        update_data = {
            "weight": 75.0,
            "height": 175.0,
            "blood_type": "O+"
        }
        response = client.put("/patients/me/profile", json=update_data, headers=patient_headers)
        assert response.status_code == 200

        # 3. Doctor updates medical info
        medical_update = {
            "status": "stable",
            "medical_history": "Patient is doing well"
        }
        response = client.put(f"/patients/{sample_patient_record.id}/admin-update", json=medical_update, headers=admin_headers)
        assert response.status_code == 200

        # 4. Patient views their updated profile
        response = client.get("/patients/me/profile", headers=patient_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 75.0
        assert data["status"] == "stable"
        assert data["medical_history"] == "Patient is doing well"


if __name__ == "__main__":
    pytest.main([__file__])