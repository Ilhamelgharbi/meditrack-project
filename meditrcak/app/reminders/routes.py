"""
Reminder API routes
Endpoints for managing medication reminders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.db import get_db
from app.auth.services import get_current_user
from app.auth.models import User
from app.reminders.services import ReminderService
from app.reminders.schemas import (
    ReminderScheduleCreate,
    ReminderScheduleUpdate,
    ReminderScheduleResponse,
    ReminderResponse,
    ReminderCancel
)
from app.reminders.models import ReminderSchedule, Reminder
from app.patients.services import PatientService


router = APIRouter(prefix="/reminders", tags=["reminders"])


# ==================== HELPER FUNCTIONS ====================

def serialize_schedule(schedule: ReminderSchedule, db: Session) -> dict:
    """Serialize reminder schedule with patient_medication details"""
    import json
    schedule_dict = {
        "id": schedule.id,
        "patient_medication_id": schedule.patient_medication_id,
        "patient_id": schedule.patient_id,
        "is_active": schedule.is_active,
        "frequency": schedule.frequency,
        "reminder_times": json.loads(schedule.reminder_times) if isinstance(schedule.reminder_times, str) else schedule.reminder_times,
        "advance_minutes": schedule.advance_minutes,
        "channel_whatsapp": schedule.channel_whatsapp,
        "channel_sms": schedule.channel_sms,
        "channel_push": schedule.channel_push,
        "channel_email": schedule.channel_email,
        "auto_skip_if_taken": schedule.auto_skip_if_taken,
        "escalate_if_missed": schedule.escalate_if_missed,
        "escalate_delay_minutes": schedule.escalate_delay_minutes,
        "quiet_hours_enabled": schedule.quiet_hours_enabled,
        "quiet_hours_start": schedule.quiet_hours_start,
        "quiet_hours_end": schedule.quiet_hours_end,
        "start_date": schedule.start_date,
        "end_date": schedule.end_date,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at
    }
    
    # Include patient_medication relationship
    from app.medications.models import PatientMedication, Medication
    patient_med = db.query(PatientMedication).filter(
        PatientMedication.id == schedule.patient_medication_id
    ).first()
    
    if patient_med:
        schedule_dict["patient_medication"] = {
            "id": patient_med.id,
            "medication_id": patient_med.medication_id,
            "dosage": patient_med.dosage,
            "instructions": patient_med.instructions,
            "times_per_day": patient_med.times_per_day,
            "start_date": patient_med.start_date,
            "end_date": patient_med.end_date,
            "status": patient_med.status,
            "confirmed_by_patient": patient_med.confirmed_by_patient
        }
        
        # Load medication details
        medication = db.query(Medication).filter(Medication.id == patient_med.medication_id).first()
        if medication:
            schedule_dict["patient_medication"]["medication"] = {
                "id": medication.id,
                "name": medication.name,
                "form": medication.form
            }
    
    return schedule_dict


# ==================== REMINDER SCHEDULE ENDPOINTS ====================

@router.post("/schedules", response_model=ReminderScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_reminder_schedule(
    schedule_data: ReminderScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new reminder schedule for a patient medication
    
    Patient can set:
    - Reminder times (e.g., ["08:00", "20:00"] for twice daily)
    - How many minutes before dose to send reminder
    - Which channels to use (WhatsApp, SMS, email, push)
    - Smart features (auto-skip if taken, escalate if missed)
    - Quiet hours
    """
    service = ReminderService(db)
    
    try:
        schedule = service.create_reminder_schedule(
            patient_id=current_user.id,
            schedule_data=schedule_data
        )
        
        return serialize_schedule(schedule, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=List[ReminderScheduleResponse])
def get_reminder_schedules(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all reminder schedules for the current patient
    
    Query params:
    - active_only: Only return active schedules
    """
    service = ReminderService(db)
    schedules = service.get_patient_reminder_schedules(
        patient_id=current_user.id,
        active_only=active_only
    )
    
    return [serialize_schedule(schedule, db) for schedule in schedules]


@router.get("/schedules/medication/{patient_medication_id}", response_model=ReminderScheduleResponse)
def get_reminder_schedule_by_medication(
    patient_medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reminder schedule for a specific patient medication"""
    service = ReminderService(db)
    schedule = service.get_reminder_schedule(
        patient_id=current_user.id,
        patient_medication_id=patient_medication_id
    )
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Reminder schedule not found"
        )
    
    return serialize_schedule(schedule, db)


@router.put("/schedules/{schedule_id}", response_model=ReminderScheduleResponse)
def update_reminder_schedule(
    schedule_id: int,
    update_data: ReminderScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing reminder schedule"""
    service = ReminderService(db)
    
    try:
        schedule = service.update_reminder_schedule(
            patient_id=current_user.id,
            schedule_id=schedule_id,
            update_data=update_data
        )
        
        return serialize_schedule(schedule, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a reminder schedule"""
    service = ReminderService(db)
    
    try:
        service.delete_reminder_schedule(
            patient_id=current_user.id,
            schedule_id=schedule_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schedules/{schedule_id}/toggle")
def toggle_reminder_schedule(
    schedule_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable or disable a reminder schedule"""
    service = ReminderService(db)
    
    try:
        schedule = service.toggle_reminder_schedule(
            patient_id=current_user.id,
            schedule_id=schedule_id,
            is_active=is_active
        )
        
        return {
            "message": f"Reminder schedule {'enabled' if is_active else 'disabled'}",
            "is_active": schedule.is_active
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== REMINDER INSTANCE ENDPOINTS ====================

@router.get("/", response_model=List[ReminderResponse])
def get_reminders(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reminders for the current patient
    
    Query params:
    - status: Filter by status (pending, sent, delivered, etc.)
    - start_date: Filter by scheduled time >= start_date
    - end_date: Filter by scheduled time <= end_date
    - limit: Maximum number of results (default 100)
    """
    service = ReminderService(db)
    reminders = service.get_patient_reminders(
        patient_id=current_user.id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return reminders


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific reminder"""
    service = ReminderService(db)
    reminder = service.get_reminder_by_id(
        patient_id=current_user.id,
        reminder_id=reminder_id
    )
    
    if not reminder:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found"
        )
    
    return reminder


@router.post("/{reminder_id}/cancel", response_model=ReminderResponse)
def cancel_reminder(
    reminder_id: int,
    cancel_data: ReminderCancel = ReminderCancel(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending reminder"""
    # Get patient profile for current user
    patient = PatientService.get_patient_by_user_id(db, current_user.id)
    
    service = ReminderService(db)
    
    try:
        reminder = service.cancel_reminder(
            patient_id=patient.id,
            reminder_id=reminder_id,
            reason=cancel_data.reason
        )
        return reminder
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schedules/{schedule_id}/generate")
def generate_reminders(
    schedule_id: int,
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate reminder instances for a schedule
    (Typically called by background job, but available for manual trigger)
    """
    service = ReminderService(db)
    
    # Verify schedule belongs to user
    schedule = service.get_reminder_schedule_by_id(schedule_id)
    if schedule.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Schedule not found or access denied")
    
    if not schedule or schedule.id != schedule_id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    reminders = service.generate_reminders_for_schedule(
        schedule_id=schedule_id,
        days_ahead=days_ahead
    )
    
    return {
        "message": f"Generated {len(reminders)} reminders",
        "count": len(reminders),
        "reminders": reminders
    }


@router.get("/stats/summary")
def get_reminder_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reminder statistics for the current patient"""
    service = ReminderService(db)
    stats = service.get_reminder_stats(
        patient_id=current_user.id,
        days=days
    )
    
    return stats
