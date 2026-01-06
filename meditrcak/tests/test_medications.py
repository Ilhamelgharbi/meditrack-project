"""
Unit tests for medication routes
"""
import pytest
from fastapi.testclient import TestClient


class TestMedicationRoutes:
    """Test cases for medication endpoints"""

    def test_get_medications_as_admin(self, client, test_admin, test_medication, admin_auth_headers):
        """Test getting all medications as admin"""
        response = client.get("/medications/", headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that our test medication is in the list
        medication_names = [m["name"] for m in data]
        assert test_medication.name in medication_names

    def test_get_medications_as_patient_forbidden(self, client, auth_headers):
        """Test that patients cannot get all medications list"""
        response = client.get("/medications/", headers=auth_headers)
        assert response.status_code == 403

    def test_get_medications_unauthenticated(self, client):
        """Test getting medications without authentication"""
        response = client.get("/medications/")
        assert response.status_code == 401

    def test_create_medication_as_admin(self, client, test_admin, admin_auth_headers):
        """Test creating a new medication as admin"""
        medication_data = {
            "name": "Test Medication",
            "dosage": "10mg",
            "frequency": "twice daily",
            "description": "Test medication for unit tests",
            "side_effects": "None",
            "interactions": "None"
        }

        response = client.post("/medications/", json=medication_data, headers=admin_auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == medication_data["name"]
        assert data["dosage"] == medication_data["dosage"]
        assert data["frequency"] == medication_data["frequency"]

    def test_create_medication_as_patient_forbidden(self, client, auth_headers):
        """Test that patients cannot create medications"""
        medication_data = {
            "name": "Test Medication",
            "dosage": "10mg",
            "frequency": "twice daily"
        }

        response = client.post("/medications/", json=medication_data, headers=auth_headers)
        assert response.status_code == 403

    def test_create_medication_duplicate_name(self, client, test_admin, test_medication, admin_auth_headers):
        """Test creating medication with duplicate name"""
        medication_data = {
            "name": test_medication.name,  # Duplicate name
            "dosage": "20mg",
            "frequency": "once daily"
        }

        response = client.post("/medications/", json=medication_data, headers=admin_auth_headers)
        assert response.status_code == 400

    def test_create_medication_invalid_data(self, client, test_admin, admin_auth_headers):
        """Test creating medication with invalid data"""
        medication_data = {
            "name": "",  # Invalid empty name
            "dosage": "10mg"
        }

        response = client.post("/medications/", json=medication_data, headers=admin_auth_headers)
        assert response.status_code == 422  # Validation error

    def test_get_specific_medication(self, client, test_medication, auth_headers):
        """Test getting specific medication details"""
        response = client.get(f"/medications/{test_medication.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_medication.id
        assert data["name"] == test_medication.name
        assert data["dosage"] == test_medication.dosage

    def test_get_nonexistent_medication(self, client, auth_headers):
        """Test getting nonexistent medication"""
        response = client.get("/medications/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_medication_as_admin(self, client, test_admin, test_medication, admin_auth_headers):
        """Test updating medication as admin"""
        update_data = {
            "name": "Updated Medication Name",
            "dosage": "20mg",
            "frequency": "three times daily",
            "description": "Updated description"
        }

        response = client.put(f"/medications/{test_medication.id}",
                            json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["dosage"] == update_data["dosage"]
        assert data["frequency"] == update_data["frequency"]

    def test_update_medication_as_patient_forbidden(self, client, test_medication, auth_headers):
        """Test that patients cannot update medications"""
        update_data = {"name": "Updated Name"}

        response = client.put(f"/medications/{test_medication.id}",
                            json=update_data, headers=auth_headers)
        assert response.status_code == 403

    def test_update_nonexistent_medication(self, client, test_admin, admin_auth_headers):
        """Test updating nonexistent medication"""
        update_data = {"name": "Updated Name"}

        response = client.put("/medications/99999", json=update_data, headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_medication_as_admin(self, client, test_admin, admin_auth_headers, test_db):
        """Test deleting medication as admin"""
        # First create a medication to delete
        medication_data = {
            "name": "Medication to Delete",
            "dosage": "5mg",
            "frequency": "once daily"
        }

        create_response = client.post("/medications/", json=medication_data, headers=admin_auth_headers)
        assert create_response.status_code == 201
        medication_id = create_response.json()["id"]

        # Now delete it
        delete_response = client.delete(f"/medications/{medication_id}", headers=admin_auth_headers)
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/medications/{medication_id}", headers=admin_auth_headers)
        assert get_response.status_code == 404

    def test_delete_medication_as_patient_forbidden(self, client, test_medication, auth_headers):
        """Test that patients cannot delete medications"""
        response = client.delete(f"/medications/{test_medication.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_nonexistent_medication(self, client, test_admin, admin_auth_headers):
        """Test deleting nonexistent medication"""
        response = client.delete("/medications/99999", headers=admin_auth_headers)
        assert response.status_code == 404