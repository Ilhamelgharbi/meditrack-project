"""
Unit tests for patient routes
"""
import pytest
from fastapi.testclient import TestClient


class TestPatientRoutes:
    """Test cases for patient endpoints"""

    def test_get_patients_as_admin(self, client, test_admin, test_user, test_patient, admin_auth_headers):
        """Test getting all patients as admin"""
        response = client.get("/patients/", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that our test patient is in the list
        patient_ids = [p["user_id"] for p in data]
        assert test_user.id in patient_ids

    def test_get_patients_as_patient_forbidden(self, client, auth_headers):
        """Test that patients cannot get all patients list"""
        response = client.get("/patients/", headers=auth_headers)
        assert response.status_code == 403

    def test_get_patients_unauthenticated(self, client):
        """Test getting patients without authentication"""
        response = client.get("/patients/")
        assert response.status_code == 401

    def test_get_own_profile(self, client, test_user, test_patient, auth_headers):
        """Test getting own patient profile"""
        response = client.get("/patients/me/profile", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["date_of_birth"] == test_patient.date_of_birth
        assert data["gender"] == test_patient.gender

    def test_get_own_profile_unauthenticated(self, client):
        """Test getting own profile without authentication"""
        response = client.get("/patients/me/profile")
        assert response.status_code == 401

    def test_update_own_profile(self, client, test_user, test_patient, auth_headers, test_db):
        """Test updating own patient profile"""
        update_data = {
            "medical_conditions": "Updated conditions",
            "allergies": "Updated allergies",
            "emergency_contact_name": "Updated Contact",
            "emergency_contact_phone": "+1234567893"
        }

        response = client.put("/patients/me/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["medical_conditions"] == update_data["medical_conditions"]
        assert data["allergies"] == update_data["allergies"]
        assert data["emergency_contact_name"] == update_data["emergency_contact_name"]
        assert data["emergency_contact_phone"] == update_data["emergency_contact_phone"]

    def test_update_own_profile_partial(self, client, test_user, test_patient, auth_headers):
        """Test partial update of own profile"""
        update_data = {"medical_conditions": "Partial update"}

        response = client.put("/patients/me/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["medical_conditions"] == update_data["medical_conditions"]
        # Other fields should remain unchanged
        assert data["allergies"] == test_patient.allergies

    def test_get_specific_patient_as_admin(self, client, test_admin, test_user, test_patient, admin_auth_headers):
        """Test getting specific patient as admin"""
        response = client.get(f"/patients/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["date_of_birth"] == test_patient.date_of_birth

    def test_get_specific_patient_as_patient_forbidden(self, client, test_user, auth_headers):
        """Test that patients cannot get other patients' profiles"""
        # Create another user ID that doesn't exist
        other_user_id = test_user.id + 999

        response = client.get(f"/patients/{other_user_id}", headers=auth_headers)
        assert response.status_code == 403

    def test_get_nonexistent_patient(self, client, test_admin, admin_auth_headers):
        """Test getting nonexistent patient"""
        response = client.get("/patients/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_admin_update_patient(self, client, test_admin, test_user, test_patient, admin_auth_headers):
        """Test admin updating patient profile"""
        update_data = {
            "medical_conditions": "Admin updated conditions",
            "allergies": "Admin updated allergies"
        }

        response = client.put(f"/patients/{test_user.id}/admin-update",
                            json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["medical_conditions"] == update_data["medical_conditions"]
        assert data["allergies"] == update_data["allergies"]

    def test_admin_update_nonexistent_patient(self, client, test_admin, admin_auth_headers):
        """Test admin updating nonexistent patient"""
        update_data = {"medical_conditions": "Test"}

        response = client.put("/patients/99999/admin-update",
                            json=update_data, headers=admin_auth_headers)
        assert response.status_code == 404

    def test_patient_update_other_patient_forbidden(self, client, auth_headers):
        """Test that patients cannot update other patients"""
        other_user_id = 99999
        update_data = {"medical_conditions": "Test"}

        response = client.put(f"/patients/{other_user_id}/admin-update",
                            json=update_data, headers=auth_headers)
        assert response.status_code == 403