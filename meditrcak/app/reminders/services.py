"""
Reminder service layer
Business logic for managing medication reminders (Twilio integration skipped)
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional, Dict
import json

logger = logging.getLogger(__name__)

from app.reminders.models import (
    Reminder, 
    ReminderSchedule, 
    ReminderStatusEnum, 
    ReminderChannelEnum,
    ReminderFrequencyEnum
)
from app.reminders.schemas import (
    ReminderScheduleCreate,
    ReminderScheduleUpdate
)
from app.medications.models import PatientMedication, Medication
from app.adherence.models import MedicationLog


class ReminderService:
    """Service for managing medication reminders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== REMINDER SCHEDULE MANAGEMENT ====================
    
    def create_reminder_schedule(
        self, 
        patient_id: int, 
        schedule_data: ReminderScheduleCreate
    ) -> ReminderSchedule:
        """Create a new reminder schedule for a patient medication"""
        
        # Verify patient owns this medication
        patient_med = self.db.query(PatientMedication).filter(
            and_(
                PatientMedication.id == schedule_data.patient_medication_id,
                PatientMedication.patient_id == patient_id
            )
        ).first()
        
        if not patient_med:
            raise ValueError("Patient medication not found or access denied")
        
        # Check if schedule already exists
        existing = self.db.query(ReminderSchedule).filter(
            ReminderSchedule.patient_medication_id == schedule_data.patient_medication_id
        ).first()
        
        if existing:
            raise ValueError("Reminder schedule already exists for this medication")
        
        # Create schedule
        schedule = ReminderSchedule(
            patient_medication_id=schedule_data.patient_medication_id,
            patient_id=patient_id,
            is_active=True,
            frequency=schedule_data.frequency,
            reminder_times=json.dumps(schedule_data.reminder_times),
            advance_minutes=schedule_data.advance_minutes,
            channel_whatsapp=schedule_data.channel_whatsapp,
            channel_sms=schedule_data.channel_sms,
            channel_push=schedule_data.channel_push,
            channel_email=schedule_data.channel_email,
            auto_skip_if_taken=schedule_data.auto_skip_if_taken,
            escalate_if_missed=schedule_data.escalate_if_missed,
            escalate_delay_minutes=schedule_data.escalate_delay_minutes,
            quiet_hours_enabled=schedule_data.quiet_hours_enabled,
            quiet_hours_start=schedule_data.quiet_hours_start,
            quiet_hours_end=schedule_data.quiet_hours_end,
            start_date=schedule_data.start_date,
            end_date=schedule_data.end_date
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        # Automatically generate reminders for the next 7 days
        try:
            self.generate_reminders_for_schedule(schedule.id, days_ahead=7)
            logger.info(f"✅ Auto-generated reminders for new schedule {schedule.id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-generate reminders for schedule {schedule.id}: {e}")
        
        return schedule
    
    def get_reminder_schedule(
        self, 
        patient_id: int, 
        patient_medication_id: int
    ) -> Optional[ReminderSchedule]:
        """Get reminder schedule for a patient medication"""
        return self.db.query(ReminderSchedule).filter(
            and_(
                ReminderSchedule.patient_medication_id == patient_medication_id,
                ReminderSchedule.patient_id == patient_id
            )
        ).first()
    
    def get_reminder_schedule_by_id(
        self, 
        schedule_id: int
    ) -> Optional[ReminderSchedule]:
        """Get reminder schedule by ID"""
        return self.db.query(ReminderSchedule).filter(
            ReminderSchedule.id == schedule_id
        ).first()
    
    def get_patient_reminder_schedules(
        self, 
        patient_id: int,
        active_only: bool = False
    ) -> List[ReminderSchedule]:
        """Get all reminder schedules for a patient"""
        query = self.db.query(ReminderSchedule).filter(
            ReminderSchedule.patient_id == patient_id
        )
        
        if active_only:
            query = query.filter(ReminderSchedule.is_active == True)
        
        return query.all()
    
    def update_reminder_schedule(
        self,
        patient_id: int,
        schedule_id: int,
        update_data: ReminderScheduleUpdate
    ) -> ReminderSchedule:
        """Update an existing reminder schedule"""
        schedule = self.db.query(ReminderSchedule).filter(
            and_(
                ReminderSchedule.id == schedule_id,
                ReminderSchedule.patient_id == patient_id
            )
        ).first()
        
        if not schedule:
            raise ValueError("Reminder schedule not found or access denied")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle reminder_times separately (needs JSON encoding)
        if 'reminder_times' in update_dict:
            update_dict['reminder_times'] = json.dumps(update_dict['reminder_times'])
        
        for key, value in update_dict.items():
            setattr(schedule, key, value)
        
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def create_individual_reminder(
        self,
        patient_id: int,
        patient_medication_id: int,
        scheduled_time: datetime,
        message_text: Optional[str] = None
    ) -> Reminder:
        """Create a single reminder instance"""
        
        # Verify patient owns this medication
        patient_med = self.db.query(PatientMedication).filter(
            and_(
                PatientMedication.id == patient_medication_id,
                PatientMedication.patient_id == patient_id
            )
        ).first()
        
        if not patient_med:
            raise ValueError("Patient medication not found or access denied")
        
        # Check if reminder already exists at this time
        existing = self.db.query(Reminder).filter(
            and_(
                Reminder.patient_medication_id == patient_medication_id,
                Reminder.scheduled_time == scheduled_time
            )
        ).first()
        
        if existing:
            raise ValueError("Reminder already exists for this medication at this time")
        
        # Generate message if not provided
        if not message_text:
            message_text = self._generate_reminder_message(patient_med, scheduled_time)
        
        # Create reminder
        reminder = Reminder(
            patient_medication_id=patient_medication_id,
            patient_id=patient_id,
            scheduled_time=scheduled_time,
            actual_dose_time=scheduled_time,  # Set to same time initially
            reminder_advance_minutes=15,  # Default
            channel=ReminderChannelEnum.whatsapp,  # Default
            status=ReminderStatusEnum.pending,
            message_text=message_text
        )
        
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def delete_reminder_schedule(
        self,
        patient_id: int,
        schedule_id: int
    ) -> bool:
        """Delete a reminder schedule"""
        schedule = self.db.query(ReminderSchedule).filter(
            and_(
                ReminderSchedule.id == schedule_id,
                ReminderSchedule.patient_id == patient_id
            )
        ).first()
        
        if not schedule:
            raise ValueError("Reminder schedule not found or access denied")
        
        self.db.delete(schedule)
        self.db.commit()
        
        return True
    
    def toggle_reminder_schedule(
        self,
        patient_id: int,
        schedule_id: int,
        is_active: bool
    ) -> ReminderSchedule:
        """Enable or disable a reminder schedule"""
        schedule = self.db.query(ReminderSchedule).filter(
            and_(
                ReminderSchedule.id == schedule_id,
                ReminderSchedule.patient_id == patient_id
            )
        ).first()
        
        if not schedule:
            raise ValueError("Reminder schedule not found or access denied")
        
        schedule.is_active = is_active
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    # ==================== REMINDER INSTANCE MANAGEMENT ====================
    
    def get_pending_reminders(
        self,
        patient_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Reminder]:
        """Get pending reminders (for background job processing)"""
        query = self.db.query(Reminder).filter(
            Reminder.status == ReminderStatusEnum.pending,
            Reminder.scheduled_time <= datetime.now()
        )
        
        if patient_id:
            query = query.filter(Reminder.patient_id == patient_id)
        
        return query.order_by(Reminder.scheduled_time).limit(limit).all()
    
    def get_patient_reminders(
        self,
        patient_id: int,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Reminder]:
        """Get reminders for a patient with optional filters"""
        query = self.db.query(Reminder).filter(
            Reminder.patient_id == patient_id
        )
        
        if status:
            query = query.filter(Reminder.status == status)
        
        if start_date:
            query = query.filter(Reminder.scheduled_time >= start_date)
        
        if end_date:
            query = query.filter(Reminder.scheduled_time <= end_date)
        
        return query.order_by(Reminder.scheduled_time.desc()).limit(limit).all()
    
    def get_reminder_by_id(
        self,
        patient_id: int,
        reminder_id: int
    ) -> Optional[Reminder]:
        """Get a specific reminder"""
        return self.db.query(Reminder).filter(
            and_(
                Reminder.id == reminder_id,
                Reminder.patient_id == patient_id
            )
        ).first()
    
    def cancel_reminder(
        self,
        patient_id: int,
        reminder_id: int,
        reason: Optional[str] = None
    ) -> Reminder:
        """Cancel a pending reminder"""
        reminder = self.db.query(Reminder).filter(
            and_(
                Reminder.id == reminder_id,
                Reminder.patient_id == patient_id
            )
        ).first()
        
        if not reminder:
            raise ValueError("Reminder not found or access denied")
        
        if reminder.status != ReminderStatusEnum.pending:
            raise ValueError("Can only cancel pending reminders")
        
        reminder.status = ReminderStatusEnum.cancelled
        reminder.response_text = reason or "Cancelled by patient"
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def mark_reminder_sent(
        self,
        reminder_id: int,
        channel: str,
        message_sid: Optional[str] = None
    ) -> Reminder:
        """Mark a reminder as sent (called by background job)"""
        reminder = self.db.query(Reminder).get(reminder_id)
        
        if not reminder:
            raise ValueError("Reminder not found")
        
        reminder.status = ReminderStatusEnum.sent
        reminder.sent_at = datetime.now()
        reminder.twilio_message_sid = message_sid
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def mark_reminder_delivered(
        self,
        message_sid: str
    ) -> Optional[Reminder]:
        """Mark reminder as delivered (Twilio webhook callback)"""
        reminder = self.db.query(Reminder).filter(
            Reminder.twilio_message_sid == message_sid
        ).first()
        
        if reminder:
            reminder.status = ReminderStatusEnum.delivered
            reminder.delivered_at = datetime.now()
            self.db.commit()
            self.db.refresh(reminder)
        
        return reminder
    
    def mark_reminder_failed(
        self,
        reminder_id: int,
        error_message: str
    ) -> Reminder:
        """Mark reminder as failed"""
        reminder = self.db.query(Reminder).get(reminder_id)
        
        if not reminder:
            raise ValueError("Reminder not found")
        
        reminder.status = ReminderStatusEnum.failed
        reminder.twilio_error_message = error_message
        reminder.retry_count += 1
        reminder.last_retry_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def record_reminder_response(
        self,
        message_sid: str,
        response_text: str
    ) -> Optional[Reminder]:
        """Record patient response to reminder (from Twilio webhook)"""
        reminder = self.db.query(Reminder).filter(
            Reminder.twilio_message_sid == message_sid
        ).first()
        
        if reminder:
            reminder.status = ReminderStatusEnum.responded
            reminder.response_text = response_text
            reminder.response_received_at = datetime.now()
            self.db.commit()
            self.db.refresh(reminder)
        
        return reminder
    
    # ==================== REMINDER GENERATION ====================
    
    def generate_reminders_for_schedule(
        self,
        schedule_id: int,
        days_ahead: int = 7
    ) -> List[Reminder]:
        """
        Generate reminder instances for a schedule
        Called by background job to create upcoming reminders
        """
        schedule = self.db.query(ReminderSchedule).get(schedule_id)
        
        if not schedule or not schedule.is_active:
            return []
        
        # Get patient medication details
        patient_med = self.db.query(PatientMedication).get(
            schedule.patient_medication_id
        )
        
        if not patient_med:
            return []
        
        # Parse reminder times
        reminder_times = json.loads(schedule.reminder_times)
        
        # Generate reminders for the next N days
        reminders_created = []
        today = datetime.now().date()
        
        for day_offset in range(days_ahead):
            target_date = today + timedelta(days=day_offset)
            
            # Check if within date range
            if schedule.end_date and target_date > schedule.end_date.date():
                continue
            
            for time_str in reminder_times:
                # Parse time
                hour, minute = map(int, time_str.split(':'))
                dose_time = datetime.combine(
                    target_date, 
                    dt_time(hour, minute)
                )
                
                # Calculate reminder time (advance_minutes before dose)
                reminder_time = dose_time - timedelta(
                    minutes=schedule.advance_minutes
                )
                
                # Skip if in the past
                if reminder_time < datetime.now():
                    continue
                
                # Check if reminder already exists
                existing = self.db.query(Reminder).filter(
                    and_(
                        Reminder.patient_medication_id == schedule.patient_medication_id,
                        Reminder.scheduled_time == reminder_time
                    )
                ).first()
                
                if existing:
                    continue
                
                # Determine primary channel
                channel = ReminderChannelEnum.push
                if schedule.channel_whatsapp:
                    channel = ReminderChannelEnum.whatsapp
                elif schedule.channel_sms:
                    channel = ReminderChannelEnum.sms
                elif schedule.channel_email:
                    channel = ReminderChannelEnum.email
                
                # Create message text
                message_text = self._generate_reminder_message(patient_med, dose_time)
                
                # Create reminder
                reminder = Reminder(
                    patient_medication_id=schedule.patient_medication_id,
                    patient_id=schedule.patient_id,
                    scheduled_time=reminder_time,
                    actual_dose_time=dose_time,
                    reminder_advance_minutes=schedule.advance_minutes,
                    channel=channel,
                    status=ReminderStatusEnum.pending,
                    message_text=message_text
                )
                
                self.db.add(reminder)
                reminders_created.append(reminder)
        
        if reminders_created:
            self.db.commit()
            for reminder in reminders_created:
                self.db.refresh(reminder)
        
        return reminders_created
    
    def _generate_reminder_message(
        self,
        patient_med: PatientMedication,
        dose_time: datetime
    ) -> str:
        """Generate reminder message text"""
        medication = patient_med.medication
        time_str = dose_time.strftime("%I:%M %p")
        
        message = f"⏰ Medication Reminder\n\n"
        message += f"💊 {medication.name}\n"
        message += f"📋 Dosage: {patient_med.dosage}\n"
        message += f"🕐 Time: {time_str}\n\n"
        message += f"Reply TAKEN when you take it, or SKIP to skip this dose."
        
        return message
    
    # ==================== STATISTICS ====================
    
    def get_reminder_stats(
        self,
        patient_id: int,
        days: int = 30
    ) -> Dict:
        """Get reminder statistics for a patient"""
        start_date = datetime.now() - timedelta(days=days)
        
        reminders = self.db.query(Reminder).filter(
            and_(
                Reminder.patient_id == patient_id,
                Reminder.scheduled_time >= start_date
            )
        ).all()
        
        total = len(reminders)
        sent = sum(1 for r in reminders if r.status in [
            ReminderStatusEnum.sent, 
            ReminderStatusEnum.delivered, 
            ReminderStatusEnum.read, 
            ReminderStatusEnum.responded
        ])
        delivered = sum(1 for r in reminders if r.status in [
            ReminderStatusEnum.delivered, 
            ReminderStatusEnum.read, 
            ReminderStatusEnum.responded
        ])
        responded = sum(1 for r in reminders if r.status == ReminderStatusEnum.responded)
        failed = sum(1 for r in reminders if r.status == ReminderStatusEnum.failed)
        
        return {
            "total_scheduled": total,
            "sent": sent,
            "delivered": delivered,
            "responded": responded,
            "failed": failed,
            "delivery_rate": (delivered / total * 100) if total > 0 else 0,
            "response_rate": (responded / delivered * 100) if delivered > 0 else 0
        }
