"""
Adherence tracking service
Business logic for medication adherence tracking and analytics
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from fastapi import HTTPException, status

from app.adherence.models import MedicationLog, AdherenceStats, AdherenceGoal, MedicationLogStatusEnum
from app.adherence.schemas import (
    MedicationLogCreate, MedicationLogUpdate, MedicationLogDetailed,
    AdherenceChartData, AdherenceDashboard, AdherenceReport
)
from app.medications.models import PatientMedication


class AdherenceService:
    """Service for adherence tracking operations"""
    
    @staticmethod
    def log_medication(db: Session, log_data: MedicationLogCreate, patient_id: int) -> MedicationLog:
        """
        Log a medication dose (taken, skipped, or missed)
        """
        # Verify patient medication exists and belongs to patient
        patient_med = db.query(PatientMedication).filter(
            PatientMedication.id == log_data.patient_medication_id,
            PatientMedication.patient_id == patient_id
        ).first()
        
        if not patient_med:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient medication not found"
            )
        
        # Check if log already exists for this scheduled time
        existing_log = db.query(MedicationLog).filter(
            MedicationLog.patient_medication_id == log_data.patient_medication_id,
            MedicationLog.scheduled_time == log_data.scheduled_time
        ).first()
        
        if existing_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Log already exists for this scheduled time. Use update endpoint to modify."
            )
        
        # Calculate if taken on time
        on_time = True
        minutes_late = None
        
        if log_data.status == MedicationLogStatusEnum.taken and log_data.actual_time:
            time_diff = (log_data.actual_time - log_data.scheduled_time).total_seconds() / 60
            minutes_late = int(abs(time_diff))
            on_time = abs(time_diff) <= 30  # Within 30 minutes is considered on time
        
        # Create log entry
        log_entry = MedicationLog(
            patient_medication_id=log_data.patient_medication_id,
            patient_id=patient_id,
            scheduled_time=log_data.scheduled_time,
            scheduled_date=log_data.scheduled_time.date(),
            status=log_data.status,
            actual_time=log_data.actual_time,
            on_time=on_time,
            minutes_late=minutes_late,
            notes=log_data.notes,
            skipped_reason=log_data.skipped_reason,
            logged_via=log_data.logged_via
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        # Trigger adherence stats recalculation (async in production)
        AdherenceService._recalculate_stats(db, patient_id, log_data.patient_medication_id)
        
        return log_entry
    
    @staticmethod
    def update_medication_log(db: Session, log_id: int, log_data: MedicationLogUpdate, patient_id: int) -> MedicationLog:
        """Update existing medication log"""
        log_entry = db.query(MedicationLog).filter(
            MedicationLog.id == log_id,
            MedicationLog.patient_id == patient_id
        ).first()
        
        if not log_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication log not found"
            )
        
        # Update fields
        if log_data.status:
            log_entry.status = log_data.status
        if log_data.actual_time:
            log_entry.actual_time = log_data.actual_time
            # Recalculate on_time and minutes_late
            time_diff = (log_data.actual_time - log_entry.scheduled_time).total_seconds() / 60
            log_entry.minutes_late = int(abs(time_diff))
            log_entry.on_time = abs(time_diff) <= 30
        if log_data.notes is not None:
            log_entry.notes = log_data.notes
        if log_data.skipped_reason is not None:
            log_entry.skipped_reason = log_data.skipped_reason
        
        db.commit()
        db.refresh(log_entry)
        
        # Trigger stats recalculation
        AdherenceService._recalculate_stats(db, patient_id, log_entry.patient_medication_id)
        
        return log_entry
    
    @staticmethod
    def get_patient_logs(
        db: Session,
        patient_id: int,
        patient_medication_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[MedicationLog]:
        """Get medication logs with medication details"""
        from app.medications.models import Medication
        
        # Join with PatientMedication and Medication to get medication details
        query = db.query(
            MedicationLog,
            PatientMedication.dosage,
            Medication.name.label('medication_name'),
            Medication.form.label('medication_form')
        ).join(
            PatientMedication, MedicationLog.patient_medication_id == PatientMedication.id
        ).join(
            Medication, PatientMedication.medication_id == Medication.id
        ).filter(MedicationLog.patient_id == patient_id)
        
        if patient_medication_id:
            query = query.filter(MedicationLog.patient_medication_id == patient_medication_id)
        
        if start_date:
            query = query.filter(MedicationLog.scheduled_date >= start_date)
        
        if end_date:
            query = query.filter(MedicationLog.scheduled_date <= end_date)
        
        if status_filter:
            query = query.filter(MedicationLog.status == status_filter)
        
        results = query.order_by(MedicationLog.scheduled_time.desc()).offset(skip).limit(limit).all()
        
        # Convert to MedicationLog objects with medication info attached
        logs_with_medication = []
        for log, dosage, medication_name, medication_form in results:
            # Add medication info as dynamic attributes
            log.medication_name = medication_name
            log.dosage = dosage
            log.medication_form = medication_form
            logs_with_medication.append(log)
        
        return logs_with_medication
    
    @staticmethod
    def get_adherence_stats(
        db: Session,
        patient_id: int,
        period_type: str = "weekly",
        patient_medication_id: Optional[int] = None
    ) -> Optional[AdherenceStats]:
        """Get adherence statistics for a period"""
        # Calculate period dates
        today = date.today()
        
        if period_type == "daily":
            period_start = today
            period_end = today
        elif period_type == "weekly":
            period_start = today - timedelta(days=7)
            period_end = today
        elif period_type == "monthly":
            period_start = today - timedelta(days=30)
            period_end = today
        else:  # overall
            period_start = date(2020, 1, 1)  # Far past
            period_end = today
        
        # Try to get existing stats - get the most recent one
        stats = db.query(AdherenceStats).filter(
            AdherenceStats.patient_id == patient_id,
            AdherenceStats.period_type == period_type,
            AdherenceStats.patient_medication_id == patient_medication_id
        ).order_by(AdherenceStats.updated_at.desc()).first()
        
        # If not exists or outdated, calculate fresh
        if not stats or not stats.updated_at or (datetime.now() - stats.updated_at).total_seconds() > 3600:
            stats = AdherenceService._calculate_stats(db, patient_id, period_type, period_start, period_end, patient_medication_id)
        
        return stats
    
    @staticmethod
    def _calculate_stats(
        db: Session,
        patient_id: int,
        period_type: str,
        period_start: date,
        period_end: date,
        patient_medication_id: Optional[int] = None
    ) -> AdherenceStats:
        """Calculate adherence statistics"""
        # Query logs for period
        query = db.query(MedicationLog).filter(
            MedicationLog.patient_id == patient_id,
            MedicationLog.scheduled_date >= period_start,
            MedicationLog.scheduled_date <= period_end
        )
        
        if patient_medication_id:
            query = query.filter(MedicationLog.patient_medication_id == patient_medication_id)
        
        logs = query.all()
        
        # Calculate metrics
        total_scheduled = len(logs)
        total_taken = sum(1 for log in logs if log.status == MedicationLogStatusEnum.taken)
        total_skipped = sum(1 for log in logs if log.status == MedicationLogStatusEnum.skipped)
        total_missed = sum(1 for log in logs if log.status == MedicationLogStatusEnum.missed)
        
        adherence_score = (total_taken / total_scheduled * 100) if total_scheduled > 0 else 0.0
        on_time_taken = sum(1 for log in logs if log.status == MedicationLogStatusEnum.taken and log.on_time)
        on_time_score = (on_time_taken / total_taken * 100) if total_taken > 0 else 0.0
        
        # Calculate streaks
        current_streak, longest_streak = AdherenceService._calculate_streaks(db, patient_id, patient_medication_id)
        
        # Update or create stats record
        stats = db.query(AdherenceStats).filter(
            AdherenceStats.patient_id == patient_id,
            AdherenceStats.period_type == period_type,
            AdherenceStats.patient_medication_id == patient_medication_id
        ).first()
        
        if stats:
            # Update existing
            stats.period_start = period_start
            stats.period_end = period_end
            stats.total_scheduled = total_scheduled
            stats.total_taken = total_taken
            stats.total_skipped = total_skipped
            stats.total_missed = total_missed
            stats.adherence_score = adherence_score
            stats.on_time_score = on_time_score
            stats.current_streak = current_streak
            stats.longest_streak = longest_streak
            stats.calculated_at = datetime.now()
        else:
            # Create new
            stats = AdherenceStats(
                patient_id=patient_id,
                patient_medication_id=patient_medication_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                total_scheduled=total_scheduled,
                total_taken=total_taken,
                total_skipped=total_skipped,
                total_missed=total_missed,
                adherence_score=adherence_score,
                on_time_score=on_time_score,
                current_streak=current_streak,
                longest_streak=longest_streak
            )
            db.add(stats)
        
        db.commit()
        db.refresh(stats)
        return stats
    
    @staticmethod
    def _calculate_streaks(db: Session, patient_id: int, patient_medication_id: Optional[int] = None) -> tuple:
        """Calculate current and longest streak"""
        # Get logs ordered by date
        query = db.query(MedicationLog).filter(MedicationLog.patient_id == patient_id)
        
        if patient_medication_id:
            query = query.filter(MedicationLog.patient_medication_id == patient_medication_id)
        
        logs = query.order_by(MedicationLog.scheduled_date.desc()).all()
        
        if not logs:
            return 0, 0
        
        # Group by date and check if all doses taken
        from collections import defaultdict
        daily_logs = defaultdict(list)
        for log in logs:
            daily_logs[log.scheduled_date].append(log)
        
        # Calculate current streak - consecutive perfect days ending with most recent perfect day
        current_streak = 0
        sorted_dates = sorted(daily_logs.keys(), reverse=True)  # Most recent first
        
        # Find the most recent perfect day and count backwards from there
        for recent_date in sorted_dates:
            day_logs = daily_logs[recent_date]
            all_taken = all(log.status == MedicationLogStatusEnum.taken for log in day_logs)
            
            if all_taken and len(day_logs) > 0:
                # Found the most recent perfect day, count streak from here
                current_streak = 1
                current_date = recent_date - timedelta(days=1)
                
                # Count consecutive perfect days backwards
                while current_date in daily_logs:
                    day_logs = daily_logs[current_date]
                    all_taken = all(log.status == MedicationLogStatusEnum.taken for log in day_logs)
                    if all_taken and len(day_logs) > 0:
                        current_streak += 1
                        current_date -= timedelta(days=1)
                    else:
                        break
                
                # Found and counted the streak, stop looking
                break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        sorted_dates = sorted(daily_logs.keys(), reverse=True)
        
        for i, current_date in enumerate(sorted_dates):
            day_logs = daily_logs[current_date]
            all_taken = all(log.status == MedicationLogStatusEnum.taken for log in day_logs)
            
            if all_taken and len(day_logs) > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        return current_streak, longest_streak
    
    @staticmethod
    def _recalculate_stats(db: Session, patient_id: int, patient_medication_id: Optional[int] = None):
        """Trigger recalculation of all stat periods"""
        for period_type in ["daily", "weekly", "monthly", "overall"]:
            today = date.today()
            
            if period_type == "daily":
                period_start, period_end = today, today
            elif period_type == "weekly":
                period_start = today - timedelta(days=7)
                period_end = today
            elif period_type == "monthly":
                period_start = today - timedelta(days=30)
                period_end = today
            else:
                period_start = date(2020, 1, 1)
                period_end = today
            
            AdherenceService._calculate_stats(db, patient_id, period_type, period_start, period_end, patient_medication_id)
    
    @staticmethod
    def delete_medication_log(db: Session, log_id: int, patient_id: int) -> None:
        """
        Delete a medication log
        Patient can only delete their own logs
        """
        log = db.query(MedicationLog).filter(MedicationLog.id == log_id).first()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication log not found"
            )
        
        # Verify ownership through patient_medication
        patient_med = db.query(PatientMedication).filter(
            PatientMedication.id == log.patient_medication_id,
            PatientMedication.patient_id == patient_id
        ).first()
        
        if not patient_med:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own medication logs"
            )
        
        db.delete(log)
        db.commit()
    
    @staticmethod
    def get_dashboard(db: Session, patient_id: int) -> AdherenceDashboard:
        """
        Get complete adherence dashboard for a patient
        """
        # Get stats for different periods
        overall_stats = AdherenceService.get_adherence_stats(db, patient_id, "overall")
        weekly_stats = AdherenceService.get_adherence_stats(db, patient_id, "weekly")
        daily_stats = AdherenceService.get_adherence_stats(db, patient_id, "daily")
        
        # Get chart data for last 7 days
        chart_data = AdherenceService.get_chart_data(db, patient_id, 7)
        
        # Get recent logs with medication details (last 10)
        recent_logs = AdherenceService.get_patient_logs(db, patient_id, limit=10)
        
        return AdherenceDashboard(
            overall_stats=overall_stats,
            weekly_stats=weekly_stats,
            daily_stats=daily_stats,
            chart_data=chart_data,
            recent_logs=recent_logs
        )
    
    @staticmethod
    def get_chart_data(db: Session, patient_id: int, days: int = 7) -> List[AdherenceChartData]:
        """
        Get adherence chart data for the last N days
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        chart_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get logs for this date
            logs = db.query(MedicationLog).filter(
                MedicationLog.patient_id == patient_id,
                MedicationLog.scheduled_date == current_date
            ).all()
            
            taken = sum(1 for log in logs if log.status == MedicationLogStatusEnum.taken)
            scheduled = len(logs)
            
            if scheduled > 0:
                score = (taken / scheduled) * 100
                status = "excellent" if score >= 90 else "good" if score >= 75 else "fair" if score >= 60 else "poor"
            else:
                score = 0
                status = "no_data"
            
            chart_data.append(AdherenceChartData(
                date=current_date,
                score=round(score, 1),
                taken=taken,
                scheduled=scheduled,
                status=status
            ))
            
            current_date += timedelta(days=1)
        
        return chart_data
