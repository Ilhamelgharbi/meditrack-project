# tests/agent/conftest.py
"""
Pytest configuration and fixtures for agent tests.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_user_context():
    """Mock user context for agent tool calls."""
    return {
        "user_id": "1",
        "token": "test_token_123",
        "role": "patient"
    }


@pytest.fixture
def mock_runtime(mock_user_context):
    """Mock ToolRuntime for testing tools."""
    runtime = MagicMock()
    runtime.config = {"configurable": mock_user_context}
    return runtime


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.query = MagicMock(return_value=MagicMock())
    session.commit = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def sample_patient():
    """Sample patient data for testing."""
    patient = MagicMock()
    patient.id = 1
    patient.user_id = 1
    patient.date_of_birth = date(1985, 5, 15)
    patient.gender = MagicMock(value="male")
    patient.blood_type = "O+"
    patient.height = 175.0
    patient.weight = 80.0
    patient.medical_history = "Hypertension diagnosed in 2020"
    patient.allergies = "Penicillin, Aspirin"
    patient.status = MagicMock(value="active")
    patient.created_at = datetime(2024, 1, 1, 10, 0, 0)
    patient.updated_at = datetime(2025, 12, 15, 14, 30, 0)
    
    # Mock user relationship
    patient.user = MagicMock()
    patient.user.full_name = "John Doe"
    patient.user.email = "john.doe@example.com"
    patient.user.phone = "+1234567890"
    patient.user.role = MagicMock(value="patient")
    
    return patient


@pytest.fixture
def sample_medications():
    """Sample medications for testing."""
    medications = []
    
    for i, (name, dosage, freq) in enumerate([
        ("Amlodipine", "5mg", 1),
        ("Lisinopril", "10mg", 1),
        ("Metformin", "500mg", 2),
    ], 1):
        med = MagicMock()
        med.id = i
        med.medication = MagicMock()
        med.medication.name = name
        med.medication.form = MagicMock(value="tablet")
        med.medication.side_effects = "May cause dizziness"
        med.medication.warnings = "Consult doctor before use"
        med.dosage = dosage
        med.times_per_day = freq
        med.instructions = "Take with food"
        med.start_date = date(2025, 1, 1)
        med.status = MagicMock(value="active")
        medications.append(med)
    
    return medications


@pytest.fixture
def sample_reminders():
    """Sample reminders for testing."""
    reminders = []
    
    times = [
        datetime(2026, 1, 5, 8, 0),
        datetime(2026, 1, 5, 14, 0),
        datetime(2026, 1, 5, 20, 0),
    ]
    
    for i, time in enumerate(times, 1):
        reminder = MagicMock()
        reminder.id = i
        reminder.patient_id = 1
        reminder.scheduled_time = time
        reminder.status = MagicMock(value="pending")
        reminder.patient_medication = MagicMock()
        reminder.patient_medication.medication = MagicMock()
        reminder.patient_medication.medication.name = f"Medication {i}"
        reminder.patient_medication.dosage = f"{i * 5}mg"
        reminders.append(reminder)
    
    return reminders


@pytest.fixture
def sample_adherence_stats():
    """Sample adherence statistics for testing."""
    return {
        "adherence_rate": 92.5,
        "doses_taken": 185,
        "doses_missed": 15,
        "total_doses": 200,
        "current_streak": 7,
        "longest_streak": 30,
        "last_dose_time": datetime(2026, 1, 5, 8, 0),
    }


@pytest.fixture
def sample_health_summary(sample_patient, sample_medications, sample_adherence_stats):
    """Complete health summary combining all data."""
    return {
        "patient": sample_patient,
        "medications": sample_medications,
        "adherence": sample_adherence_stats,
        "vitals": {
            "height": 175.0,
            "weight": 80.0,
            "bmi": 26.1,
            "blood_pressure": "120/80",
        },
        "allergies": ["Penicillin", "Aspirin"],
        "conditions": ["Hypertension"],
    }


# Agent-specific fixtures

@pytest.fixture
def mock_groq_model():
    """Mock Groq LLM model."""
    with patch('app.agent.patient_agent.ChatGroq') as mock:
        model = MagicMock()
        model.invoke = MagicMock(return_value=MagicMock(content="Test response"))
        mock.return_value = model
        yield model


@pytest.fixture
def all_patient_tools():
    """List of all patient tool names."""
    return [
        # Profile
        "get_my_profile",
        "get_my_vitals",
        "update_my_profile",
        "update_my_vitals",
        # Medications
        "get_my_medications",
        "get_active_medications",
        "get_pending_medications",
        "confirm_medication",
        "get_inactive_medications",
        # Adherence
        "get_my_adherence_stats",
        # Reminders
        "get_my_reminders",
        "set_medication_reminder",
        # Medical
        "get_my_medical_history",
        "get_my_allergies",
        "get_my_health_summary",
        # Logging
        "log_medication_taken",
        "log_medication_skipped",
        "get_recent_medication_logs",
    ]


@pytest.fixture
def test_questions():
    """All 13 test questions for the patient agent."""
    return [
        {"id": 1, "question": "What is my profile information?", "expected_tool": "get_my_profile", "category": "profile"},
        {"id": 2, "question": "Tell me about myself and my medical history", "expected_tool": "get_my_profile", "category": "profile"},
        {"id": 3, "question": "What are my current vital signs?", "expected_tool": "get_my_vitals", "category": "vitals"},
        {"id": 4, "question": "Show me my latest measurements", "expected_tool": "get_my_vitals", "category": "vitals"},
        {"id": 5, "question": "What are my medication reminders for today?", "expected_tool": "get_my_reminders", "category": "reminders"},
        {"id": 6, "question": "When should I take my next medication?", "expected_tool": "get_my_reminders", "category": "reminders"},
        {"id": 7, "question": "Can you set a reminder for my medication at 8 AM?", "expected_tool": "set_medication_reminder", "category": "reminders"},
        {"id": 8, "question": "What medications am I currently taking?", "expected_tool": "get_active_medications", "category": "medications"},
        {"id": 9, "question": "Do I have any pending medications to confirm?", "expected_tool": "get_pending_medications", "category": "medications"},
        {"id": 10, "question": "Show me all my medications including stopped ones", "expected_tool": "get_my_medications", "category": "medications"},
        {"id": 11, "question": "How well am I taking my medications?", "expected_tool": "get_my_adherence_stats", "category": "medications"},
        {"id": 12, "question": "Give me a complete overview of my health", "expected_tool": "get_my_health_summary", "category": "health_summary"},
        {"id": 13, "question": "What allergies do I have?", "expected_tool": "get_my_allergies", "category": "health_summary"},
    ]
