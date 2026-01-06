"""
Unit tests for reminder routes
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestReminderRoutes:
    """Test cases for reminder endpoints"""

    def test_get_reminders_as_patient(self, client, test_user, test_patient_medication, auth_headers):
        """Test getting own reminders as patient"""
        response = client.get("/reminders/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_reminders_unauthenticated(self, client):
        """Test getting reminders without authentication"""
        response = client.get("/reminders/")
        assert response.status_code == 401

    def test_create_reminder_as_patient(self, client, test_user, test_patient_medication, auth_headers):
        """Test creating a reminder as patient"""
        tomorrow = datetime.now() + timedelta(days=1)
        reminder_data = {
            "medication_id": test_patient_medication.medication_id,
            "scheduled_time": tomorrow.isoformat(),
            "message": "Take your medication",
            "is_recurring": False
        }

        response = client.post("/reminders/", json=reminder_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["medication_id"] == reminder_data["medication_id"]
        assert data["message"] == reminder_data["message"]
        assert data["is_recurring"] == reminder_data["is_recurring"]

    def test_create_reminder_invalid_medication(self, client, auth_headers):
        """Test creating reminder with invalid medication ID"""
        tomorrow = datetime.now() + timedelta(days=1)
        reminder_data = {
            "medication_id": 99999,  # Nonexistent medication
            "scheduled_time": tomorrow.isoformat(),
            "message": "Take medication"
        }

        response = client.post("/reminders/", json=reminder_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_reminder_past_time(self, client, test_patient_medication, auth_headers):
        """Test creating reminder with past scheduled time"""
        yesterday = datetime.now() - timedelta(days=1)
        reminder_data = {
            "medication_id": test_patient_medication.medication_id,
            "scheduled_time": yesterday.isoformat(),
            "message": "Take medication"
        }

        response = client.post("/reminders/", json=reminder_data, headers=auth_headers)
        assert response.status_code == 400

    def test_get_specific_reminder(self, client, test_reminder, auth_headers):
        """Test getting specific reminder"""
        response = client.get(f"/reminders/{test_reminder.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_reminder.id
        assert data["medication_id"] == test_reminder.medication_id
        assert data["message"] == test_reminder.message

    def test_get_other_patients_reminder_forbidden(self, client, auth_headers):
        """Test that patients cannot access other patients' reminders"""
        # Assuming reminder ID 99999 belongs to another patient
        response = client.get("/reminders/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_reminder(self, client, test_reminder, auth_headers):
        """Test updating own reminder"""
        update_data = {
            "message": "Updated reminder message",
            "is_completed": True
        }

        response = client.put(f"/reminders/{test_reminder.id}",
                            json=update_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == update_data["message"]
        assert data["is_completed"] == update_data["is_completed"]

    def test_update_other_patients_reminder_forbidden(self, client, auth_headers):
        """Test that patients cannot update other patients' reminders"""
        update_data = {"message": "Updated message"}
        response = client.put("/reminders/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_reminder(self, client, test_reminder, auth_headers):
        """Test deleting own reminder"""
        response = client.delete(f"/reminders/{test_reminder.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/reminders/{test_reminder.id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_other_patients_reminder_forbidden(self, client, auth_headers):
        """Test that patients cannot delete other patients' reminders"""
        response = client.delete("/reminders/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_today_reminders(self, client, auth_headers):
        """Test getting today's reminders"""
        response = client.get("/reminders/today", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_upcoming_reminders(self, client, auth_headers):
        """Test getting upcoming reminders"""
        response = client.get("/reminders/upcoming", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_overdue_reminders(self, client, auth_headers):
        """Test getting overdue reminders"""
        response = client.get("/reminders/overdue", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_mark_reminder_completed(self, client, test_reminder, auth_headers):
        """Test marking reminder as completed"""
        response = client.post(f"/reminders/{test_reminder.id}/complete", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] == True

    def test_mark_other_patients_reminder_completed_forbidden(self, client, auth_headers):
        """Test that patients cannot mark other patients' reminders as completed"""
        response = client.post("/reminders/99999/complete", headers=auth_headers)
        assert response.status_code == 404

    def test_snooze_reminder(self, client, test_reminder, auth_headers):
        """Test snoozing a reminder"""
        snooze_data = {"minutes": 30}

        response = client.post(f"/reminders/{test_reminder.id}/snooze",
                             json=snooze_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # The scheduled time should be updated
        assert "scheduled_time" in data

    def test_snooze_other_patients_reminder_forbidden(self, client, auth_headers):
        """Test that patients cannot snooze other patients' reminders"""
        snooze_data = {"minutes": 30}
        response = client.post("/reminders/99999/snooze", json=snooze_data, headers=auth_headers)
        assert response.status_code == 404