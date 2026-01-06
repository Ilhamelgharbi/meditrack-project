"""
Adherence analytics service
Provides analytics calculations for medication adherence
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_, case
from typing import List, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.analytics.schemas.adherence import (
    AdherenceOverview,
    AdherenceTrend,
    PatientAdherenceSummary,
    MedicationAdherenceDetail,
    AdherenceStats
)
from app.adherence.models import MedicationLog, MedicationLogStatusEnum
from app.medications.models import PatientMedication, MedicationStatusEnum
from app.patients.models import Patient
from app.auth.models import User


class AdherenceAnalyticsService:
    """Service for calculating adherence analytics"""

    @staticmethod
    def get_adherence_overview(db: Session, start_date: date, end_date: date) -> AdherenceOverview:
        """Calculate overall adherence statistics for a date range"""

        # Get total patients with medications
        total_patients = db.query(func.count(func.distinct(PatientMedication.patient_id))).filter(
            PatientMedication.status.in_([MedicationStatusEnum.active, MedicationStatusEnum.pending]),
            PatientMedication.start_date <= end_date
        ).scalar() or 0

        # Get patients with logs in the period
        patients_with_logs = db.query(func.count(func.distinct(MedicationLog.patient_id))).filter(
            MedicationLog.scheduled_date.between(start_date, end_date)
        ).scalar() or 0

        # Calculate total doses and adherence
        dose_stats = db.query(
            func.count(MedicationLog.id).label('total_doses'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.taken, 1), else_=0)).label('taken'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.missed, 1), else_=0)).label('missed'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.skipped, 1), else_=0)).label('skipped')
        ).filter(
            MedicationLog.scheduled_date.between(start_date, end_date)
        ).first()

        total_doses = dose_stats.total_doses or 0
        taken_doses = dose_stats.taken or 0
        missed_doses = dose_stats.missed or 0
        skipped_doses = dose_stats.skipped or 0

        # Calculate adherence rate
        adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0

        # Calculate adherence distribution
        adherence_distribution = {"excellent": 0, "good": 0, "poor": 0}

        # Get adherence rates per patient
        patient_adherence = db.query(
            MedicationLog.patient_id,
            (func.sum(case((MedicationLog.status == MedicationLogStatusEnum.taken, 1), else_=0)) /
             func.count(MedicationLog.id) * 100).label('adherence_rate')
        ).filter(
            MedicationLog.scheduled_date.between(start_date, end_date)
        ).group_by(MedicationLog.patient_id).all()

        for _, rate in patient_adherence:
            if rate >= 90:
                adherence_distribution["excellent"] += 1
            elif rate >= 70:
                adherence_distribution["good"] += 1
            else:
                adherence_distribution["poor"] += 1

        return AdherenceOverview(
            total_patients=total_patients,
            patients_with_logs=patients_with_logs,
            average_adherence_rate=round(adherence_rate, 2),
            adherence_distribution=adherence_distribution,
            total_doses_scheduled=total_doses,
            total_doses_taken=taken_doses,
            total_doses_missed=missed_doses,
            total_doses_skipped=skipped_doses,
            period_start=start_date,
            period_end=end_date
        )

    @staticmethod
    def get_adherence_trends(db: Session, start_date: date, end_date: date, patient_id: Optional[int] = None) -> List[AdherenceTrend]:
        """Get adherence trends over time"""

        query = db.query(
            MedicationLog.scheduled_date,
            func.count(MedicationLog.id).label('total_doses'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.taken, 1), else_=0)).label('taken'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.missed, 1), else_=0)).label('missed'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.skipped, 1), else_=0)).label('skipped')
        ).filter(
            MedicationLog.scheduled_date.between(start_date, end_date)
        )

        if patient_id:
            query = query.filter(MedicationLog.patient_id == patient_id)

        query = query.group_by(MedicationLog.scheduled_date).order_by(MedicationLog.scheduled_date)

        results = query.all()
        trends = []

        for row in results:
            total_doses = row.total_doses or 0
            taken_doses = row.taken or 0
            adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0

            trends.append(AdherenceTrend(
                date=row.scheduled_date,
                adherence_rate=round(adherence_rate, 2),
                doses_scheduled=total_doses,
                doses_taken=taken_doses,
                doses_missed=row.missed or 0,
                doses_skipped=row.skipped or 0
            ))

        return trends

    @staticmethod
    def get_patient_adherence_summary(db: Session, limit: int = 50, min_adherence: Optional[float] = None) -> List[PatientAdherenceSummary]:
        """Get adherence summary for patients"""

        # Get patients with medications
        patients_query = db.query(
            User.id.label('patient_id'),
            User.full_name.label('patient_name'),
            func.count(PatientMedication.id).label('total_medications')
        ).join(
            PatientMedication, User.id == PatientMedication.patient_id
        ).filter(
            PatientMedication.status.in_([MedicationStatusEnum.active, MedicationStatusEnum.pending])
        ).group_by(User.id, User.full_name)

        if min_adherence is not None:
            # This would require a subquery for adherence calculation
            # For now, return all patients
            pass

        patients = patients_query.limit(limit).all()

        summaries = []
        for patient in patients:
            # Get adherence stats for this patient (last 30 days)
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            dose_stats = db.query(
                func.count(MedicationLog.id).label('total_doses'),
                func.sum(case((MedicationLog.status == MedicationLogStatusEnum.taken, 1), else_=0)).label('taken'),
                func.sum(case((MedicationLog.status == MedicationLogStatusEnum.missed, 1), else_=0)).label('missed'),
                func.sum(case((MedicationLog.status == MedicationLogStatusEnum.skipped, 1), else_=0)).label('skipped'),
                func.max(MedicationLog.scheduled_date).label('last_log_date')
            ).filter(
                MedicationLog.patient_id == patient.patient_id,
                MedicationLog.scheduled_date.between(start_date, end_date)
            ).first()

            total_doses = dose_stats.total_doses or 0
            taken_doses = dose_stats.taken or 0
            adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0

            summaries.append(PatientAdherenceSummary(
                patient_id=patient.patient_id,
                patient_name=patient.patient_name,
                adherence_rate=round(adherence_rate, 2),
                total_medications=patient.total_medications,
                doses_scheduled=total_doses,
                doses_taken=taken_doses,
                doses_missed=dose_stats.missed or 0,
                doses_skipped=dose_stats.skipped or 0,
                last_log_date=dose_stats.last_log_date
            ))

        return summaries

    @staticmethod
    def get_medication_adherence_details(db: Session, medication_id: Optional[int] = None, limit: int = 50) -> List[MedicationAdherenceDetail]:
        """Get adherence details for medications"""

        query = db.query(
            PatientMedication.medication_id,
            PatientMedication.id.label('patient_medication_id'),
            func.count(MedicationLog.id).label('total_logs'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.taken, 1), else_=0)).label('taken'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.missed, 1), else_=0)).label('missed'),
            func.sum(case((MedicationLog.status == MedicationLogStatusEnum.skipped, 1), else_=0)).label('skipped')
        ).join(
            MedicationLog, PatientMedication.id == MedicationLog.patient_medication_id
        ).filter(
            PatientMedication.status == MedicationStatusEnum.active
        ).group_by(PatientMedication.medication_id, PatientMedication.id)

        if medication_id:
            query = query.filter(PatientMedication.medication_id == medication_id)

        results = query.limit(limit).all()

        # Group by medication
        med_stats = defaultdict(lambda: {
            'total_patients': 0,
            'total_logs': 0,
            'taken': 0,
            'missed': 0,
            'skipped': 0
        })

        for row in results:
            med_stats[row.medication_id]['total_patients'] += 1
            med_stats[row.medication_id]['total_logs'] += row.total_logs or 0
            med_stats[row.medication_id]['taken'] += row.taken or 0
            med_stats[row.medication_id]['missed'] += row.missed or 0
            med_stats[row.medication_id]['skipped'] += row.skipped or 0

        details = []
        for med_id, stats in med_stats.items():
            medication = db.query(PatientMedication).join(PatientMedication.medication).filter(
                PatientMedication.medication_id == med_id
            ).first()

            if medication:
                total_logs = stats['total_logs']
                adherence_rate = (stats['taken'] / total_logs * 100) if total_logs > 0 else 0

                details.append(MedicationAdherenceDetail(
                    medication_id=med_id,
                    medication_name=medication.medication.name,
                    total_patients=stats['total_patients'],
                    average_adherence_rate=round(adherence_rate, 2),
                    doses_scheduled=total_logs,
                    doses_taken=stats['taken'],
                    doses_missed=stats['missed'],
                    doses_skipped=stats['skipped'],
                    most_common_skip_reason=None  # Would need additional query
                ))

        return details[:limit]

    @staticmethod
    def get_adherence_stats(db: Session, start_date: date, end_date: date, patient_id: Optional[int] = None) -> AdherenceStats:
        """Get detailed adherence statistics"""

        query = db.query(MedicationLog).filter(
            MedicationLog.scheduled_date.between(start_date, end_date)
        )

        if patient_id:
            query = query.filter(MedicationLog.patient_id == patient_id)

        logs = query.all()

        if not logs:
            return AdherenceStats(
                overall_adherence=0,
                on_time_adherence=0,
                weekday_adherence=0,
                weekend_adherence=0,
                adherence_by_hour={},
                adherence_by_day={},
                improvement_trend=0,
                consistency_score=0
            )

        # Calculate overall adherence
        total_logs = len(logs)
        taken_logs = len([log for log in logs if log.status == MedicationLogStatusEnum.taken])
        overall_adherence = (taken_logs / total_logs * 100) if total_logs > 0 else 0

        # Calculate on-time adherence
        on_time_taken = len([log for log in logs if log.status == MedicationLogStatusEnum.taken and log.on_time])
        on_time_adherence = (on_time_taken / total_logs * 100) if total_logs > 0 else 0

        # Calculate weekday vs weekend adherence
        weekday_logs = [log for log in logs if log.scheduled_date.weekday() < 5]
        weekend_logs = [log for log in logs if log.scheduled_date.weekday() >= 5]

        weekday_taken = len([log for log in weekday_logs if log.status == MedicationLogStatusEnum.taken])
        weekend_taken = len([log for log in weekend_logs if log.status == MedicationLogStatusEnum.taken])

        weekday_adherence = (weekday_taken / len(weekday_logs) * 100) if weekday_logs else 0
        weekend_adherence = (weekend_taken / len(weekend_logs) * 100) if weekend_logs else 0

        # Calculate adherence by hour
        adherence_by_hour = defaultdict(lambda: {'total': 0, 'taken': 0})
        for log in logs:
            hour = log.scheduled_time.hour
            adherence_by_hour[hour]['total'] += 1
            if log.status == MedicationLogStatusEnum.taken:
                adherence_by_hour[hour]['taken'] += 1

        hour_rates = {}
        for hour, stats in adherence_by_hour.items():
            rate = (stats['taken'] / stats['total'] * 100) if stats['total'] > 0 else 0
            hour_rates[str(hour)] = round(rate, 2)

        # Calculate adherence by day of week
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        adherence_by_day = defaultdict(lambda: {'total': 0, 'taken': 0})
        for log in logs:
            day = day_names[log.scheduled_date.weekday()]
            adherence_by_day[day]['total'] += 1
            if log.status == MedicationLogStatusEnum.taken:
                adherence_by_day[day]['taken'] += 1

        day_rates = {}
        for day, stats in adherence_by_day.items():
            rate = (stats['taken'] / stats['total'] * 100) if stats['total'] > 0 else 0
            day_rates[day] = round(rate, 2)

        # Calculate improvement trend (simplified - would need more complex analysis)
        improvement_trend = 0  # Placeholder

        # Calculate consistency score (simplified)
        consistency_score = overall_adherence * 0.8  # Placeholder

        return AdherenceStats(
            overall_adherence=round(overall_adherence, 2),
            on_time_adherence=round(on_time_adherence, 2),
            weekday_adherence=round(weekday_adherence, 2),
            weekend_adherence=round(weekend_adherence, 2),
            adherence_by_hour=hour_rates,
            adherence_by_day=day_rates,
            improvement_trend=round(improvement_trend, 2),
            consistency_score=round(consistency_score, 2)
        )