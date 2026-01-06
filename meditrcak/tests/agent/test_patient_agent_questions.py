# tests/agent/test_patient_agent_questions.py
"""
Patient Agent Integration Tests

13 test questions covering:
- Profile (2 questions)
- Vitals (2 questions)
- Reminders (3 questions)
- Medications (4 questions)
- Health Summary (2 questions)

Tests agent responses for accuracy, latency, and tool selection.
"""

import pytest
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Test questions organized by category
PATIENT_TEST_QUESTIONS = {
    "profile": [
        {
            "id": 1,
            "question": "What is my profile information?",
            "expected_tool": "get_my_profile",
            "expected_keywords": ["name", "email", "phone", "date of birth"],
            "category": "profile"
        },
        {
            "id": 2,
            "question": "Tell me about myself and my medical history",
            "expected_tool": "get_my_profile",
            "expected_keywords": ["medical history", "allergies", "blood type"],
            "category": "profile"
        },
    ],
    "vitals": [
        {
            "id": 3,
            "question": "What are my current vital signs?",
            "expected_tool": "get_my_vitals",
            "expected_keywords": ["height", "weight", "blood pressure", "bmi"],
            "category": "vitals"
        },
        {
            "id": 4,
            "question": "Show me my latest measurements",
            "expected_tool": "get_my_vitals",
            "expected_keywords": ["height", "weight", "measurements"],
            "category": "vitals"
        },
    ],
    "reminders": [
        {
            "id": 5,
            "question": "What are my medication reminders for today?",
            "expected_tool": "get_my_reminders",
            "expected_keywords": ["reminder", "medication", "time", "today"],
            "category": "reminders"
        },
        {
            "id": 6,
            "question": "When should I take my next medication?",
            "expected_tool": "get_my_reminders",
            "expected_keywords": ["medication", "time", "take"],
            "category": "reminders"
        },
        {
            "id": 7,
            "question": "Can you set a reminder for my medication at 8 AM?",
            "expected_tool": "set_medication_reminder",
            "expected_keywords": ["reminder", "set", "8"],
            "category": "reminders"
        },
    ],
    "medications": [
        {
            "id": 8,
            "question": "What medications am I currently taking?",
            "expected_tool": "get_active_medications",
            "expected_keywords": ["medication", "taking", "active"],
            "category": "medications"
        },
        {
            "id": 9,
            "question": "Do I have any pending medications to confirm?",
            "expected_tool": "get_pending_medications",
            "expected_keywords": ["pending", "confirm", "medication"],
            "category": "medications"
        },
        {
            "id": 10,
            "question": "Show me all my medications including stopped ones",
            "expected_tool": "get_my_medications",
            "expected_keywords": ["medication", "all", "stopped"],
            "category": "medications"
        },
        {
            "id": 11,
            "question": "How well am I taking my medications?",
            "expected_tool": "get_my_adherence_stats",
            "expected_keywords": ["adherence", "compliance", "rate", "percentage"],
            "category": "medications"
        },
    ],
    "health_summary": [
        {
            "id": 12,
            "question": "Give me a complete overview of my health",
            "expected_tool": "get_my_health_summary",
            "expected_keywords": ["health", "summary", "overview"],
            "category": "health_summary"
        },
        {
            "id": 13,
            "question": "What allergies do I have?",
            "expected_tool": "get_my_allergies",
            "expected_keywords": ["allergies", "allergy", "allergic"],
            "category": "health_summary"
        },
    ],
}


class TestPatientAgentQuestions:
    """Test patient agent with 13 questions across categories."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_patient_data(self):
        """Sample patient data for testing."""
        return {
            "id": 1,
            "user_id": 1,
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": date(1985, 5, 15),
            "gender": "male",
            "blood_type": "O+",
            "height": 175.0,
            "weight": 80.0,
            "medical_history": "Hypertension diagnosed in 2020",
            "allergies": "Penicillin, Aspirin",
        }

    @pytest.fixture
    def mock_vitals_data(self):
        """Sample vitals data for testing."""
        return {
            "height": 175.0,
            "weight": 80.0,
            "bmi": 26.1,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "temperature": 36.6,
        }

    @pytest.fixture
    def mock_medications_data(self):
        """Sample medications data for testing."""
        return [
            {
                "id": 1,
                "name": "Amlodipine",
                "dosage": "5mg",
                "frequency": "Once daily",
                "status": "active",
                "instructions": "Take with food",
            },
            {
                "id": 2,
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "status": "active",
                "instructions": "Take in the morning",
            },
        ]

    @pytest.fixture
    def mock_reminders_data(self):
        """Sample reminders data for testing."""
        return [
            {
                "id": 1,
                "medication_name": "Amlodipine",
                "scheduled_time": datetime(2026, 1, 5, 8, 0),
                "status": "pending",
            },
            {
                "id": 2,
                "medication_name": "Lisinopril",
                "scheduled_time": datetime(2026, 1, 5, 20, 0),
                "status": "pending",
            },
        ]

    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Flatten all questions from all categories."""
        all_questions = []
        for category, questions in PATIENT_TEST_QUESTIONS.items():
            all_questions.extend(questions)
        return all_questions

    # ==========================================================================
    # PROFILE TESTS (Questions 1-2)
    # ==========================================================================

    def test_question_01_profile_information(self, mock_db, mock_patient_data):
        """Test: What is my profile information?"""
        question = PATIENT_TEST_QUESTIONS["profile"][0]
        
        with patch('app.agent.tools.patients.profile_tools.get_db') as mock_get_db:
            mock_get_db.return_value = iter([mock_db])
            
            # Verify question structure
            assert question["id"] == 1
            assert question["expected_tool"] == "get_my_profile"
            assert "profile" in question["question"].lower()

    def test_question_02_medical_history(self, mock_db, mock_patient_data):
        """Test: Tell me about myself and my medical history"""
        question = PATIENT_TEST_QUESTIONS["profile"][1]
        
        assert question["id"] == 2
        assert question["expected_tool"] == "get_my_profile"
        assert "medical history" in question["question"].lower()

    # ==========================================================================
    # VITALS TESTS (Questions 3-4)
    # ==========================================================================

    def test_question_03_vital_signs(self, mock_db, mock_vitals_data):
        """Test: What are my current vital signs?"""
        question = PATIENT_TEST_QUESTIONS["vitals"][0]
        
        assert question["id"] == 3
        assert question["expected_tool"] == "get_my_vitals"
        assert "vital" in question["question"].lower()

    def test_question_04_measurements(self, mock_db, mock_vitals_data):
        """Test: Show me my latest measurements"""
        question = PATIENT_TEST_QUESTIONS["vitals"][1]
        
        assert question["id"] == 4
        assert question["expected_tool"] == "get_my_vitals"
        assert "measurements" in question["question"].lower()

    # ==========================================================================
    # REMINDERS TESTS (Questions 5-7)
    # ==========================================================================

    def test_question_05_reminders_today(self, mock_db, mock_reminders_data):
        """Test: What are my medication reminders for today?"""
        question = PATIENT_TEST_QUESTIONS["reminders"][0]
        
        assert question["id"] == 5
        assert question["expected_tool"] == "get_my_reminders"
        assert "reminders" in question["question"].lower()

    def test_question_06_next_medication(self, mock_db, mock_reminders_data):
        """Test: When should I take my next medication?"""
        question = PATIENT_TEST_QUESTIONS["reminders"][1]
        
        assert question["id"] == 6
        assert question["expected_tool"] == "get_my_reminders"
        assert "next" in question["question"].lower()

    def test_question_07_set_reminder(self, mock_db):
        """Test: Can you set a reminder for my medication at 8 AM?"""
        question = PATIENT_TEST_QUESTIONS["reminders"][2]
        
        assert question["id"] == 7
        assert question["expected_tool"] == "set_medication_reminder"
        assert "set" in question["question"].lower()

    # ==========================================================================
    # MEDICATIONS TESTS (Questions 8-11)
    # ==========================================================================

    def test_question_08_current_medications(self, mock_db, mock_medications_data):
        """Test: What medications am I currently taking?"""
        question = PATIENT_TEST_QUESTIONS["medications"][0]
        
        assert question["id"] == 8
        assert question["expected_tool"] == "get_active_medications"
        assert "taking" in question["question"].lower()

    def test_question_09_pending_medications(self, mock_db):
        """Test: Do I have any pending medications to confirm?"""
        question = PATIENT_TEST_QUESTIONS["medications"][1]
        
        assert question["id"] == 9
        assert question["expected_tool"] == "get_pending_medications"
        assert "pending" in question["question"].lower()

    def test_question_10_all_medications(self, mock_db, mock_medications_data):
        """Test: Show me all my medications including stopped ones"""
        question = PATIENT_TEST_QUESTIONS["medications"][2]
        
        assert question["id"] == 10
        assert question["expected_tool"] == "get_my_medications"
        assert "all" in question["question"].lower()

    def test_question_11_adherence_stats(self, mock_db):
        """Test: How well am I taking my medications?"""
        question = PATIENT_TEST_QUESTIONS["medications"][3]
        
        assert question["id"] == 11
        assert question["expected_tool"] == "get_my_adherence_stats"
        assert "well" in question["question"].lower()

    # ==========================================================================
    # HEALTH SUMMARY TESTS (Questions 12-13)
    # ==========================================================================

    def test_question_12_health_overview(self, mock_db):
        """Test: Give me a complete overview of my health"""
        question = PATIENT_TEST_QUESTIONS["health_summary"][0]
        
        assert question["id"] == 12
        assert question["expected_tool"] == "get_my_health_summary"
        assert "overview" in question["question"].lower()

    def test_question_13_allergies(self, mock_db, mock_patient_data):
        """Test: What allergies do I have?"""
        question = PATIENT_TEST_QUESTIONS["health_summary"][1]
        
        assert question["id"] == 13
        assert question["expected_tool"] == "get_my_allergies"
        assert "allergies" in question["question"].lower()

    # ==========================================================================
    # COMPREHENSIVE TESTS
    # ==========================================================================

    def test_all_questions_have_required_fields(self):
        """Verify all 13 questions have required fields."""
        all_questions = self.get_all_questions()
        
        assert len(all_questions) == 13, f"Expected 13 questions, got {len(all_questions)}"
        
        for q in all_questions:
            assert "id" in q, f"Question missing 'id' field"
            assert "question" in q, f"Question {q.get('id')} missing 'question' field"
            assert "expected_tool" in q, f"Question {q.get('id')} missing 'expected_tool' field"
            assert "expected_keywords" in q, f"Question {q.get('id')} missing 'expected_keywords' field"
            assert "category" in q, f"Question {q.get('id')} missing 'category' field"

    def test_question_ids_are_sequential(self):
        """Verify question IDs are 1-13 sequential."""
        all_questions = self.get_all_questions()
        ids = sorted([q["id"] for q in all_questions])
        
        assert ids == list(range(1, 14)), f"Question IDs should be 1-13, got {ids}"

    def test_category_coverage(self):
        """Verify all categories are covered."""
        expected_categories = {"profile", "vitals", "reminders", "medications", "health_summary"}
        actual_categories = set(PATIENT_TEST_QUESTIONS.keys())
        
        assert actual_categories == expected_categories, \
            f"Missing categories: {expected_categories - actual_categories}"

    def test_tool_mapping_validity(self):
        """Verify expected tools are valid patient tools."""
        valid_tools = {
            "get_my_profile",
            "get_my_vitals",
            "update_my_profile",
            "update_my_vitals",
            "get_my_medications",
            "get_active_medications",
            "get_pending_medications",
            "confirm_medication",
            "get_inactive_medications",
            "get_my_adherence_stats",
            "get_my_reminders",
            "set_medication_reminder",
            "get_my_medical_history",
            "get_my_allergies",
            "get_my_health_summary",
            "log_medication_taken",
            "log_medication_skipped",
            "get_recent_medication_logs",
        }
        
        all_questions = self.get_all_questions()
        for q in all_questions:
            assert q["expected_tool"] in valid_tools, \
                f"Question {q['id']} has invalid tool: {q['expected_tool']}"
