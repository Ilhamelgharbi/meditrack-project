# app/agent/tools/patients/__init__.py
"""
Direct imports of essential patient tools for the patient agent.
"""

# Profile tools
from .profile_tools import get_my_profile, get_my_vitals, update_my_profile, update_my_vitals

# Medication tools
from .medication_tools import (
    get_my_medications,
    get_active_medications,
    get_pending_medications,
    confirm_medication,
    get_inactive_medications
)

# Adherence tools
from .adherence_tools import get_my_adherence_stats

# Reminder tools
from .reminder_tools import get_my_reminders, set_medication_reminder

# Medical tools
from .medical_tools import get_my_medical_history, get_my_allergies, get_my_health_summary

# Logging tools
from .logging_tools import log_medication_taken, log_medication_skipped, get_recent_medication_logs

# Export all essential tools
__all__ = [
    # Profile tools
    "get_my_profile",
    "get_my_vitals",
    "update_my_profile",
    "update_my_vitals",

    # Medication tools
    "get_my_medications",
    "get_active_medications",
    "get_pending_medications",
    "confirm_medication",
    "get_inactive_medications",

    # Adherence tools
    "get_my_adherence_stats",

    # Reminder tools
    "get_my_reminders",
    "set_medication_reminder",

    # Medical tools
    "get_my_medical_history",
    "get_my_allergies",
    "get_my_health_summary",

    # Logging tools
    "log_medication_taken",
    "log_medication_skipped",
    "get_recent_medication_logs",
]