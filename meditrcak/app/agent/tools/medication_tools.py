# app/agent/tools/medication_tools.py
"""
Medication Management Tools for AI Agent.

Uses direct database access (same as database_tools.py) to avoid
HTTP deadlock when agent and API run on the same server.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database.db import get_db
from app.patients.models import Patient
from app.medications.models import Medication, PatientMedication
from app.adherence.models import MedicationLog
from app.reminders.models import ReminderSchedule

logger = logging.getLogger(__name__)


class Context(TypedDict):
    """Context passed to tools from the agent runtime."""
    user_id: str
    token: str


def _get_db_session() -> Session:
    """Get a database session."""
    return next(get_db())


# ============================================================================
# MEDICATION LIST TOOLS
# ============================================================================

@tool("list_medications", description="List all medications for the patient. Optionally filter by status: 'pending', 'active', or 'stopped'.")
def list_medications(
    runtime: ToolRuntime[Context],
    status: Optional[str] = None
) -> str:
    """
    List all medications for the patient.
    
    Args:
        status: Filter by status - 'pending', 'active', or 'stopped'. Leave empty for all.
    
    Returns:
        List of medications with name, dosage, frequency, and status.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        # Query patient medications
        query = db.query(PatientMedication).filter(PatientMedication.patient_id == patient.id)
        if status:
            query = query.filter(PatientMedication.status == status)
        
        patient_meds = query.all()
        
        if not patient_meds:
            if status:
                return f"You don't have any {status} medications."
            return "You don't have any medications on record."
        
        # Format the response
        lines = [f"📋 **Your Medications** ({len(patient_meds)} total):\n"]
        
        for i, pm in enumerate(patient_meds, 1):
            medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
            med_name = medication.name if medication else "Unknown"
            
            status_emoji = {
                "active": "✅",
                "pending": "⏳",
                "stopped": "⛔"
            }.get(pm.status, "❓")
            
            lines.append(
                f"{i}. {status_emoji} **{med_name}**\n"
                f"   • Dosage: {pm.dosage or 'N/A'}\n"
                f"   • Instructions: {pm.instructions or 'Take as directed'}\n"
                f"   • Status: {pm.status}\n"
            )
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in list_medications: {e}")
        return f"Sorry, I couldn't fetch your medications: {str(e)}"
    finally:
        db.close()


@tool("get_medication_details", description="Get detailed information about a specific medication including dosage, instructions, and side effects.")
def get_medication_details(
    runtime: ToolRuntime[Context],
    medication_name: str
) -> str:
    """
    Get detailed information about a specific medication.
    
    Args:
        medication_name: The name of the medication to look up.
    
    Returns:
        Detailed information including dosage, instructions, side effects.
    """
    db = _get_db_session()
    
    try:
        # Search for the medication by name
        medication = db.query(Medication).filter(
            Medication.name.ilike(f"%{medication_name}%")
        ).first()
        
        if not medication:
            return f"I couldn't find any medication matching '{medication_name}'."
        
        return (
            f"💊 **{medication.name}**\n\n"
            f"**Form:** {medication.form or 'N/A'}\n"
            f"**Default Dosage:** {medication.default_dosage or 'N/A'}\n\n"
            f"**Side Effects:**\n{medication.side_effects or 'Consult your pharmacist.'}\n\n"
            f"**Warnings:**\n{medication.warnings or 'Take as prescribed by your doctor.'}"
        )
        
    except Exception as e:
        logger.error(f"Error in get_medication_details: {e}")
        return f"Sorry, I couldn't get medication details: {str(e)}"
    finally:
        db.close()


# ============================================================================
# MEDICATION ACTION TOOLS
# ============================================================================

@tool("accept_medication", description="Accept a pending medication prescription. Changes status from 'pending' to 'active'.")
def accept_medication(
    runtime: ToolRuntime[Context],
    medication_id: int
) -> str:
    """
    Accept a pending medication that was prescribed to you.
    Changes the medication status from 'pending' to 'active'.
    
    Args:
        medication_id: The ID of the patient_medication to accept.
    
    Returns:
        Confirmation message.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        # Find the patient medication
        pm = db.query(PatientMedication).filter(
            PatientMedication.id == medication_id,
            PatientMedication.patient_id == patient.id
        ).first()
        
        if not pm:
            return "Medication not found or doesn't belong to you."
        
        if pm.status != "pending":
            return f"This medication is already {pm.status}."
        
        pm.status = "active"
        pm.confirmed_by_patient = True
        db.commit()
        
        medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
        med_name = medication.name if medication else "the medication"
        
        return (
            f"✅ **Medication Accepted!**\n\n"
            f"**{med_name}** has been added to your active medications. "
            f"You'll start receiving reminders based on your schedule."
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in accept_medication: {e}")
        return f"Sorry, I couldn't accept the medication: {str(e)}"
    finally:
        db.close()


@tool("log_medication_action", description="Log when you take, skip, or miss a medication dose. Use action: 'taken', 'skipped', or 'missed'.")
def log_medication_action(
    runtime: ToolRuntime[Context],
    medication_id: int,
    action: str,
    notes: Optional[str] = None
) -> str:
    """
    Log when you take, skip, or miss a medication dose.
    
    Args:
        medication_id: The ID of the patient_medication.
        action: One of 'taken', 'skipped', or 'missed'.
        notes: Optional notes about why you skipped or any observations.
    
    Returns:
        Confirmation of the logged action.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        # Validate action
        valid_actions = ["taken", "skipped", "missed"]
        if action not in valid_actions:
            return f"Invalid action. Use one of: {', '.join(valid_actions)}"
        
        # Find the patient medication
        pm = db.query(PatientMedication).filter(
            PatientMedication.id == medication_id,
            PatientMedication.patient_id == patient.id
        ).first()
        
        if not pm:
            return "Medication not found or doesn't belong to you."
        
        # Create log entry
        log = MedicationLog(
            patient_medication_id=pm.id,
            patient_id=patient.user_id,
            scheduled_time=datetime.utcnow(),
            scheduled_date=datetime.utcnow().date(),
            status=action,
            actual_time=datetime.utcnow() if action == 'taken' else None,
            notes=notes,
            logged_via='agent'
        )
        db.add(log)
        db.commit()
        
        medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
        med_name = medication.name if medication else "Medication"
        
        action_emoji = {
            "taken": "✅",
            "skipped": "⏭️",
            "missed": "❌"
        }.get(action, "📝")
        
        return (
            f"{action_emoji} **{med_name} - {action.title()}!**\n\n"
            f"I've recorded that you {action} your dose at {datetime.now().strftime('%I:%M %p')}.\n"
            f"{f'Note: {notes}' if notes else ''}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in log_medication_action: {e}")
        return f"Sorry, I couldn't log the medication action: {str(e)}"
    finally:
        db.close()


# ============================================================================
# REMINDER TOOLS
# ============================================================================

@tool("list_reminders", description="List all your medication reminders for today.")
def list_reminders(
    runtime: ToolRuntime[Context],
    include_completed: bool = False
) -> str:
    """
    List all your medication reminders for today.
    
    Args:
        include_completed: Whether to include reminders you've already completed.
    
    Returns:
        List of reminders with times and medications.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        # Get today's reminders
        today = datetime.now().date()
        
        reminders = db.query(ReminderSchedule).join(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            PatientMedication.status == "active"
        ).all()
        
        if not reminders:
            return "You don't have any reminders scheduled."
        
        lines = [f"⏰ **Your Reminders** ({len(reminders)} scheduled):\n"]
        
        for reminder in reminders:
            pm = db.query(PatientMedication).filter(PatientMedication.id == reminder.patient_medication_id).first()
            medication = db.query(Medication).filter(Medication.id == pm.medication_id).first() if pm else None
            med_name = medication.name if medication else "Unknown"
            
            # reminder_times is a JSON list like ["08:00", "20:00"]
            times = reminder.reminder_times if reminder.reminder_times else []
            time_str = ", ".join(times) if times else "N/A"
            
            status_icon = "🔔" if reminder.is_active else "🔕"
            lines.append(f"• {status_icon} **{med_name}** - {time_str}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in list_reminders: {e}")
        return f"Sorry, I couldn't fetch your reminders: {str(e)}"
    finally:
        db.close()


@tool("get_upcoming_doses", description="Get medications you need to take in the next few hours.")
def get_upcoming_doses(
    runtime: ToolRuntime[Context],
    hours_ahead: int = 4
) -> str:
    """
    Get medications you need to take in the next few hours.
    
    Args:
        hours_ahead: Number of hours to look ahead (default 4).
    
    Returns:
        List of upcoming doses with times.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        
        # Get active medications with reminders
        patient_meds = db.query(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            PatientMedication.status == "active"
        ).all()
        
        if not patient_meds:
            return f"No medications scheduled in the next {hours_ahead} hours. 👍"
        
        lines = [f"⏰ **Upcoming in the next {hours_ahead} hours:**\n"]
        
        for pm in patient_meds:
            medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
            med_name = medication.name if medication else "Unknown"
            lines.append(f"• **{med_name}** - {pm.dosage or 'As directed'}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in get_upcoming_doses: {e}")
        return f"Sorry, I couldn't fetch upcoming doses: {str(e)}"
    finally:
        db.close()


# ============================================================================
# ADHERENCE TOOLS
# ============================================================================

@tool("get_adherence_stats", description="Get your medication adherence statistics for the past days.")
def get_adherence_stats(
    runtime: ToolRuntime[Context],
    days: int = 7
) -> str:
    """
    Get your medication adherence statistics.
    
    Args:
        days: Number of days to calculate stats for (default 7).
    
    Returns:
        Adherence percentage, streak, and breakdown by medication.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        # Get logs from the past N days
        cutoff = datetime.now() - timedelta(days=days)
        
        logs = db.query(MedicationLog).join(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            MedicationLog.scheduled_time >= cutoff,
            MedicationLog.reminder_id.isnot(None)  # Only count scheduled doses, not manual logs
        ).all()
        
        if not logs:
            return f"No medication history found for the last {days} days."
        
        # Calculate stats
        total = len(logs)
        taken = sum(1 for log in logs if (log.status.value if hasattr(log.status, 'value') else log.status) == "taken")
        adherence = (taken / total * 100) if total > 0 else 0
        
        # Determine encouragement message based on adherence
        if adherence >= 90:
            emoji, message = "🌟", "Excellent work! Keep it up!"
        elif adherence >= 70:
            emoji, message = "👍", "Good job! Try to stay consistent."
        elif adherence >= 50:
            emoji, message = "💪", "You can do better! Set reminders to help."
        else:
            emoji, message = "🎯", "Let's work on improving together!"
        
        lines = [
            f"{emoji} **Adherence Report (Last {days} days)**\n",
            f"📊 **Overall Adherence:** {adherence:.1f}%",
            f"📈 **Doses Taken:** {taken} / {total}",
            f"\n_{message}_"
        ]
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in get_adherence_stats: {e}")
        return f"Sorry, I couldn't fetch adherence stats: {str(e)}"
    finally:
        db.close()


@tool("get_medication_history", description="Get your medication taking history for the past days.")
def get_medication_history(
    runtime: ToolRuntime[Context],
    medication_id: Optional[int] = None,
    days: int = 7
) -> str:
    """
    Get your medication taking history.
    
    Args:
        medication_id: Optional ID to filter to a specific medication.
        days: Number of days of history to retrieve (default 7).
    
    Returns:
        History of doses taken, skipped, or missed.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        cutoff = datetime.now() - timedelta(days=days)
        
        query = db.query(MedicationLog).join(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            MedicationLog.scheduled_time >= cutoff
        )
        
        if medication_id:
            query = query.filter(PatientMedication.id == medication_id)
        
        logs = query.order_by(MedicationLog.scheduled_time.desc()).all()
        
        if not logs:
            return f"No medication history found for the last {days} days."
        
        lines = [f"📜 **Medication History (Last {days} days):**\n"]
        
        current_date = None
        for log in logs:
            log_date = log.scheduled_time.strftime("%B %d, %Y")
            
            # Group by date
            if log_date != current_date:
                current_date = log_date
                lines.append(f"\n**{log_date}:**")
            
            pm = db.query(PatientMedication).filter(PatientMedication.id == log.patient_medication_id).first()
            medication = db.query(Medication).filter(Medication.id == pm.medication_id).first() if pm else None
            med_name = medication.name if medication else "Unknown"
            
            status_emoji = {
                "taken": "✅",
                "skipped": "⏭️",
                "missed": "❌"
            }.get(log.status.value if hasattr(log.status, 'value') else log.status, "❓")
            
            time_str = log.scheduled_time.strftime("%I:%M %p")
            manual_note = " (manual)" if log.reminder_id is None else ""
            lines.append(f"  {status_emoji} {time_str} - {med_name}{manual_note}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in get_medication_history: {e}")
        return f"Sorry, I couldn't fetch medication history: {str(e)}"
    finally:
        db.close()


# ============================================================================
# DASHBOARD TOOL
# ============================================================================

@tool("get_medication_dashboard", description="Get a complete overview of your medication status - active medications, today's reminders, and adherence stats.")
def get_medication_dashboard(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get a complete overview of your medication status.
    
    Returns:
        Complete medication dashboard with all relevant information.
    """
    user_id = runtime.context["user_id"]
    db = _get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
        if not patient:
            return "Patient profile not found."
        
        lines = ["📊 **Your Medication Dashboard**\n", "=" * 40 + "\n"]
        
        # Active Medications Section
        lines.append("💊 **Active Medications:**")
        active_meds = db.query(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            PatientMedication.status == "active"
        ).all()
        
        if active_meds:
            for pm in active_meds[:5]:
                medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
                med_name = medication.name if medication else "Unknown"
                lines.append(f"  • {med_name} - {pm.dosage or 'N/A'}")
        else:
            lines.append("  No active medications")
        
        lines.append("")
        
        # Pending Medications Section
        pending_meds = db.query(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            PatientMedication.status == "pending"
        ).all()
        
        if pending_meds:
            lines.append("⏳ **Pending Medications (need your approval):**")
            for pm in pending_meds:
                medication = db.query(Medication).filter(Medication.id == pm.medication_id).first()
                med_name = medication.name if medication else "Unknown"
                lines.append(f"  • {med_name} (ID: {pm.id})")
            lines.append("")
        
        # Adherence Section
        cutoff = datetime.now() - timedelta(days=7)
        logs = db.query(MedicationLog).join(PatientMedication).filter(
            PatientMedication.patient_id == patient.id,
            MedicationLog.scheduled_time >= cutoff,
            MedicationLog.reminder_id.isnot(None)  # Only count scheduled doses
        ).all()
        
        lines.append("📈 **7-Day Adherence:**")
        if logs:
            total = len(logs)
            taken = sum(1 for log in logs if log.status == "taken")
            adherence = (taken / total * 100) if total > 0 else 0
            lines.append(f"  Overall: {adherence:.0f}% ({taken}/{total} doses taken)")
        else:
            lines.append("  No data available")
        
        lines.append("\n" + "=" * 40)
        lines.append("_Ask me about any medication for more details!_")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in get_medication_dashboard: {e}")
        return f"Sorry, I couldn't fetch your dashboard: {str(e)}"
    finally:
        db.close()


# ============================================================================
# EXPORT ALL TOOLS
# ============================================================================

__all__ = [
    "list_medications",
    "get_medication_details",
    "accept_medication",
    "log_medication_action",
    "list_reminders",
    "get_upcoming_doses",
    "get_adherence_stats",
    "get_medication_history",
    "get_medication_dashboard",
]
