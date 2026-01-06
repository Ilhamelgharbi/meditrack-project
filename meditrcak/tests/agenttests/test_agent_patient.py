"""
Unit tests for patient agent tools
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.tools import ToolRuntime

from app.agent.tools.patients.profile_tools import (
    get_my_profile,
    get_my_vitals,
    update_my_profile,
    update_my_vitals
)
from app.agent.tools.patients.medication_tools import (
    get_my_medications,
    get_active_medications,
    get_pending_medications,
    confirm_medication,
    get_inactive_medications
)
from app.agent.tools.patients.adherence_tools import get_my_adherence_stats
from app.agent.tools.patients.reminder_tools import (
    get_my_reminders,
    set_medication_reminder
)
from app.agent.tools.patients.medical_tools import (
    get_my_medical_history,
    get_my_allergies,
    get_my_health_summary
)
from app.agent.tools.patients.logging_tools import (
    log_medication_taken,
    log_medication_skipped,
    get_recent_medication_logs
)


class TestPatientAgentTools:
    """Test cases for patient agent tools"""

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock ToolRuntime with patient context"""
        runtime = Mock(spec=ToolRuntime)
        runtime.config = {
            "configurable": {
                "user_id": "1",
                "token": "test_token",
                "role": "patient"
            }
        }
        return runtime

    @pytest.fixture
    def mock_runtime_doctor(self):
        """Create a mock ToolRuntime with doctor context"""
        runtime = Mock(spec=ToolRuntime)
        runtime.config = {
            "configurable": {
                "user_id": "2",
                "token": "doctor_token",
                "role": "doctor"
            }
        }
        return runtime

    # ============================================================================
    # PROFILE TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.profile_tools.PatientService.get_patient_by_user_id')
    @patch('app.database.db.get_db')
    def test_get_my_profile_success(self, mock_get_db, mock_get_patient, mock_runtime):
        """Test successful profile retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock the patient object returned by the service
        mock_patient = Mock()
        mock_patient.user.full_name = "John Doe"
        mock_patient.user.email = "john@example.com"
        mock_patient.user.phone = "123-456-7890"
        mock_patient.user.role.value = "patient"
        mock_patient.date_of_birth.isoformat.return_value = "1990-01-01"
        mock_patient.gender.value = "male"
        mock_patient.blood_type = "O+"
        mock_patient.height = 175
        mock_patient.weight = 70
        mock_patient.status.value = "active"
        mock_patient.medical_history = "Hypertension"
        mock_patient.allergies = "None"
        mock_patient.created_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_patient.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_get_patient.return_value = mock_patient

        result = get_my_profile.func(mock_runtime)

        assert isinstance(result, str)
        assert "John Doe" in result
        assert "1990-01-01" in result

    @patch('app.agent.tools.patients.profile_tools.PatientService')
    @patch('app.database.db.get_db')
    def test_get_my_profile_service_error(self, mock_get_db, mock_patient_service, mock_runtime):
        """Test profile retrieval with service error"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_profile.side_effect = Exception("Database error")
        mock_patient_service.return_value = mock_service_instance

        result = get_my_profile.func(mock_runtime)

        assert isinstance(result, str)
        assert "error" in result.lower() or "failed" in result.lower()

    @patch('app.agent.tools.patients.profile_tools.PatientService')
    @patch('app.database.db.get_db')
    def test_get_my_vitals_success(self, mock_get_db, mock_patient_service, mock_runtime):
        """Test successful vitals retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_vitals.return_value = {
            "blood_pressure": "120/80",
            "heart_rate": 72,
            "temperature": 98.6,
            "weight": 180,
            "height": 70
        }
        mock_patient_service.return_value = mock_service_instance

        result = get_my_vitals.func(mock_runtime)

        assert isinstance(result, str)
        assert "120/80" in result
        assert "72" in result

    @patch('app.agent.tools.patients.profile_tools.PatientService')
    @patch('app.database.db.get_db')
    def test_update_my_profile_success(self, mock_get_db, mock_patient_service, mock_runtime):
        """Test successful profile update"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.update_patient_profile.return_value = {
            "user_id": 1,
            "full_name": "John Smith",
            "email": "johnsmith@example.com"
        }
        mock_patient_service.return_value = mock_service_instance

        result = update_my_profile.func(
            mock_runtime,
            full_name="John Smith",
            phone="555-0123"
        )

        assert isinstance(result, str)
        assert "successfully updated" in result.lower()

    # ============================================================================
    # MEDICATION TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.medication_tools.PatientMedicationService')
    @patch('app.database.db.get_db')
    def test_get_my_medications_success(self, mock_get_db, mock_med_service, mock_runtime):
        """Test successful medication retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_medications.return_value = [
            {
                "id": 1,
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "status": "active"
            },
            {
                "id": 2,
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "status": "active"
            }
        ]
        mock_med_service.return_value = mock_service_instance

        result = get_my_medications.func(mock_runtime)

        assert isinstance(result, str)
        assert "Lisinopril" in result
        assert "Metformin" in result

    @patch('app.agent.tools.patients.medication_tools.PatientMedicationService')
    @patch('app.database.db.get_db')
    def test_get_active_medications_success(self, mock_get_db, mock_med_service, mock_runtime):
        """Test successful active medication retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_medications.return_value = [
            {
                "id": 1,
                "name": "Lisinopril",
                "status": "active"
            }
        ]
        mock_med_service.return_value = mock_service_instance

        result = get_active_medications.func(mock_runtime)

        assert isinstance(result, str)
        assert "Lisinopril" in result

    @patch('app.agent.tools.patients.medication_tools.PatientMedicationService')
    @patch('app.database.db.get_db')
    def test_confirm_medication_success(self, mock_get_db, mock_med_service, mock_runtime):
        """Test successful medication confirmation"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.confirm_medication.return_value = {
            "id": 1,
            "name": "Lisinopril",
            "status": "active"
        }
        mock_med_service.return_value = mock_service_instance

        result = confirm_medication.func(
            mock_runtime,
            medication_id=1
        )

        assert isinstance(result, str)
        assert "confirmed" in result.lower() or "success" in result.lower()

    @patch('app.agent.tools.patients.medication_tools.PatientMedicationService')
    @patch('app.database.db.get_db')
    def test_confirm_medication_invalid_id(self, mock_get_db, mock_med_service, mock_runtime):
        """Test medication confirmation with invalid ID"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.confirm_medication.side_effect = ValueError("Medication not found")
        mock_med_service.return_value = mock_service_instance

        result = confirm_medication.func(
            mock_runtime,
            medication_id=999
        )

        assert isinstance(result, str)
        assert "not found" in result.lower() or "error" in result.lower()

    # ============================================================================
    # ADHERENCE TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.adherence_tools.AdherenceService')
    @patch('app.database.db.get_db')
    def test_get_my_adherence_stats_success(self, mock_get_db, mock_adherence_service, mock_runtime):
        """Test successful adherence stats retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_adherence_stats.return_value = {
            "overall_adherence": 85.5,
            "medications_taken": 45,
            "total_medications": 50,
            "missed_medications": 5,
            "period": "last_30_days"
        }
        mock_adherence_service.return_value = mock_service_instance

        result = get_my_adherence_stats.func(mock_runtime)

        assert isinstance(result, str)
        assert "85.5%" in result or "85.5" in result
        assert "45" in result
        assert "50" in result

    # ============================================================================
    # REMINDER TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.reminder_tools.ReminderService')
    @patch('app.database.db.get_db')
    def test_get_my_reminders_success(self, mock_get_db, mock_reminder_service, mock_runtime):
        """Test successful reminder retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_reminders.return_value = [
            {
                "id": 1,
                "medication_name": "Lisinopril",
                "scheduled_time": "2024-01-15T08:00:00Z",
                "status": "pending"
            }
        ]
        mock_reminder_service.return_value = mock_service_instance

        result = get_my_reminders.func(mock_runtime)

        assert isinstance(result, str)
        assert "Lisinopril" in result

    @patch('app.agent.tools.patients.reminder_tools.ReminderService')
    @patch('app.database.db.get_db')
    def test_set_medication_reminder_success(self, mock_get_db, mock_reminder_service, mock_runtime):
        """Test successful reminder setting"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.create_medication_reminder.return_value = {
            "id": 1,
            "medication_id": 1,
            "scheduled_time": "2024-01-15T08:00:00Z"
        }
        mock_reminder_service.return_value = mock_service_instance

        result = set_medication_reminder.func(
            mock_runtime,
            medication_id=1,
            reminder_time="08:00",
            frequency="daily"
        )

        assert isinstance(result, str)
        assert "success" in result.lower() or "created" in result.lower()

    # ============================================================================
    # MEDICAL TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.medical_tools.Patient')
    @patch('app.database.db.get_db')
    def test_get_my_medical_history_success(self, mock_get_db, mock_patient_model, mock_runtime):
        """Test successful medical history retrieval"""
        # Mock the database session and query
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_patient_instance = Mock()
        mock_patient_instance.medical_history = "Diagnosed with hypertension in 2020"
        mock_patient_instance.status = Mock()
        mock_patient_instance.status.value = "stable"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.first.return_value = mock_patient_instance
        mock_db.query.return_value = mock_query

        result = get_my_medical_history.func(mock_runtime)

        assert isinstance(result, str)
        assert "hypertension" in result

    @patch('app.agent.tools.patients.medical_tools.Patient')
    @patch('app.database.db.get_db')
    def test_get_my_allergies_success(self, mock_get_db, mock_patient_model, mock_runtime):
        """Test successful allergies retrieval"""
        # Mock the database session and query
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_patient_instance = Mock()
        mock_patient_instance.allergies = "Penicillin, Shellfish"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.first.return_value = mock_patient_instance
        mock_db.query.return_value = mock_query

        result = get_my_allergies.func(mock_runtime)

        assert isinstance(result, str)
        assert "Penicillin" in result

    @patch('app.agent.tools.patients.medical_tools.Patient')
    @patch('app.database.db.get_db')
    def test_get_my_health_summary_success(self, mock_get_db, mock_patient_model, mock_runtime):
        """Test successful health summary retrieval"""
        # Mock the database session and query
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_patient_instance = Mock()
        mock_patient_instance.medical_history = "Hypertension"
        mock_patient_instance.status = Mock()
        mock_patient_instance.status.value = "well_controlled"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.first.return_value = mock_patient_instance
        mock_db.query.return_value = mock_query

        result = get_my_health_summary.func(mock_runtime)

        assert isinstance(result, str)
        assert "Hypertension" in result

    # ============================================================================
    # LOGGING TOOLS TESTS
    # ============================================================================

    @patch('app.agent.tools.patients.logging_tools.MedicationLog')
    @patch('app.agent.tools.patients.logging_tools.PatientMedication')
    @patch('app.database.db.get_db')
    def test_log_medication_taken_success(self, mock_get_db, mock_patient_med, mock_med_log, mock_runtime):
        """Test successful medication logging"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock the medication lookup
        mock_medication = Mock()
        mock_medication.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_medication
        mock_db.query.return_value = mock_query

        result = log_medication_taken.func(
            mock_runtime,
            medication_name="Lisinopril",
            notes="Taken with breakfast"
        )

        assert isinstance(result, str)
        assert "success" in result.lower() or "logged" in result.lower()

    @patch('app.agent.tools.patients.logging_tools.MedicationLog')
    @patch('app.agent.tools.patients.logging_tools.PatientMedication')
    @patch('app.database.db.get_db')
    def test_log_medication_skipped_success(self, mock_get_db, mock_patient_med, mock_med_log, mock_runtime):
        """Test successful medication skip logging"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock the medication lookup
        mock_medication = Mock()
        mock_medication.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_medication
        mock_db.query.return_value = mock_query

        result = log_medication_skipped.func(
            mock_runtime,
            medication_name="Lisinopril",
            reason="Forgot"
        )

        assert isinstance(result, str)
        assert "skipped" in result.lower() or "logged" in result.lower()

    @patch('app.agent.tools.patients.logging_tools.MedicationLog')
    @patch('app.database.db.get_db')
    def test_get_recent_medication_logs_success(self, mock_get_db, mock_med_log, mock_runtime):
        """Test successful recent logs retrieval"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock the log query results
        mock_log1 = Mock()
        mock_log1.medication_name = "Lisinopril"
        mock_log1.taken_at = "2024-01-15T08:05:00Z"
        mock_log1.status = Mock()
        mock_log1.status.value = "taken"

        mock_log2 = Mock()
        mock_log2.medication_name = "Metformin"
        mock_log2.taken_at = "2024-01-15T12:00:00Z"
        mock_log2.status = Mock()
        mock_log2.status.value = "taken"

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_log1, mock_log2]
        mock_db.query.return_value = mock_query

        result = get_recent_medication_logs.func(
            mock_runtime,
            days=7
        )

        assert isinstance(result, str)
        assert "Lisinopril" in result
        assert "Metformin" in result

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    @patch('app.database.db.get_db')
    def test_tools_with_invalid_runtime_config(self, mock_get_db):
        """Test tools handle missing runtime config gracefully"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        runtime = Mock(spec=ToolRuntime)
        runtime.config = {}  # Missing configurable

        with pytest.raises(KeyError):
            get_my_profile.func(runtime)

    @patch('app.agent.tools.patients.profile_tools.PatientService')
    @patch('app.database.db.get_db')
    def test_tools_with_non_patient_role(self, mock_get_db, mock_service, mock_runtime_doctor):
        """Test tools work with different roles (should still work for doctors accessing patient data)"""
        # Mock the database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_patient_profile.return_value = {"user_id": 1}
        mock_service.return_value = mock_service_instance

        result = get_my_profile.func(mock_runtime_doctor)

        assert isinstance(result, str)
        # Should work even for doctors (they might need to access patient data)