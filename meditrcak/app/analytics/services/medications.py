"""
Medication analytics service
Provides analytics calculations for medication usage and management
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case
from typing import List, Optional
from datetime import date, timedelta


from app.analytics.schemas.medications import (
    MedicationUsageStats,
    MedicationPopularity,
    MedicationStatusDistribution,
    MedicationAnalyticsSummary,
    TopPrescribedMedications
)
from app.medications.models import Medication, PatientMedication, MedicationStatusEnum, MedicationFormEnum
from app.auth.models import User


class MedicationAnalyticsService:
    """Service for calculating medication analytics"""

    @staticmethod
    def get_medication_usage_stats(db: Session, start_date: date, end_date: date) -> MedicationUsageStats:
        """Calculate overall medication usage statistics"""

        # Total medications in catalog
        total_medications = db.query(func.count(Medication.id)).scalar() or 0

        # Total patient-medication assignments
        total_patient_medications = db.query(func.count(PatientMedication.id)).scalar() or 0

        # Active patient-medication assignments
        active_patient_medications = db.query(func.count(PatientMedication.id)).filter(
            PatientMedication.status == MedicationStatusEnum.active
        ).scalar() or 0

        # Average medications per patient
        patients_with_meds = db.query(func.count(func.distinct(PatientMedication.patient_id))).filter(
            PatientMedication.status.in_([MedicationStatusEnum.active, MedicationStatusEnum.pending])
        ).scalar() or 0

        average_medications_per_patient = (active_patient_medications / patients_with_meds) if patients_with_meds > 0 else 0

        # Most common forms
        form_stats = db.query(
            Medication.form,
            func.count(Medication.id).label('count')
        ).group_by(Medication.form).all()

        most_common_forms = {}
        for form, count in form_stats:
            if form:
                most_common_forms[form.value] = count

        # Prescriptions by doctor
        doctor_stats = db.query(
            User.full_name,
            func.count(PatientMedication.id).label('count')
        ).join(
            PatientMedication, User.id == PatientMedication.assigned_by_doctor
        ).group_by(User.id, User.full_name).order_by(func.count(PatientMedication.id).desc()).limit(10).all()

        prescriptions_by_doctor = {}
        for doctor_name, count in doctor_stats:
            prescriptions_by_doctor[doctor_name or 'Unknown'] = count

        return MedicationUsageStats(
            total_medications=total_medications,
            total_patient_medications=total_patient_medications,
            active_patient_medications=active_patient_medications,
            average_medications_per_patient=round(average_medications_per_patient, 1),
            most_common_forms=most_common_forms,
            prescriptions_by_doctor=prescriptions_by_doctor
        )

    @staticmethod
    def get_medication_popularity(db: Session, limit: int = 20, min_prescriptions: Optional[int] = None) -> List[MedicationPopularity]:
        """Get most popular medications by prescription count"""

        query = db.query(
            Medication.id.label('medication_id'),
            Medication.name.label('medication_name'),
            Medication.form,
            func.count(PatientMedication.id).label('total_prescriptions'),
            func.sum(case((PatientMedication.status == MedicationStatusEnum.active, 1), else_=0)).label('active_prescriptions'),
            func.count(func.distinct(PatientMedication.patient_id)).label('unique_patients'),
            func.mode(PatientMedication.dosage).label('average_dosage'),
            User.full_name.label('created_by')
        ).join(
            PatientMedication, Medication.id == PatientMedication.medication_id
        ).join(
            User, Medication.created_by == User.id
        ).group_by(Medication.id, Medication.name, Medication.form, User.full_name)

        if min_prescriptions:
            query = query.having(func.count(PatientMedication.id) >= min_prescriptions)

        query = query.order_by(func.count(PatientMedication.id).desc()).limit(limit)

        results = query.all()

        popularity_list = []
        for row in results:
            popularity_list.append(MedicationPopularity(
                medication_id=row.medication_id,
                medication_name=row.medication_name,
                form=row.form.value if row.form else 'unknown',
                total_prescriptions=row.total_prescriptions or 0,
                active_prescriptions=row.active_prescriptions or 0,
                unique_patients=row.unique_patients or 0,
                average_dosage=row.average_dosage,
                created_by=row.created_by or 'Unknown'
            ))

        return popularity_list

    @staticmethod
    def get_medication_status_distribution(db: Session) -> MedicationStatusDistribution:
        """Get distribution of medications by status"""

        status_stats = db.query(
            PatientMedication.status,
            func.count(PatientMedication.id).label('count')
        ).group_by(PatientMedication.status).all()

        status_counts = {'active': 0, 'pending': 0, 'stopped': 0}
        total = 0

        for status, count in status_stats:
            if status:
                status_counts[status.value] = count
            total += count

        status_percentages = {}
        for status, count in status_counts.items():
            status_percentages[status] = round((count / total * 100), 1) if total > 0 else 0

        return MedicationStatusDistribution(
            active=status_counts['active'],
            pending=status_counts['pending'],
            stopped=status_counts['stopped'],
            total=total,
            status_percentages=status_percentages
        )

    @staticmethod
    def get_top_prescribed_medications(db: Session, start_date: date, end_date: date, limit: int = 10) -> List[TopPrescribedMedications]:
        """Get top prescribed medications in the specified period"""

        query = db.query(
            Medication.id.label('medication_id'),
            Medication.name.label('medication_name'),
            Medication.form,
            func.count(PatientMedication.id).label('prescriptions_count'),
            func.count(func.distinct(PatientMedication.patient_id)).label('unique_patients'),
            func.avg(PatientMedication.times_per_day).label('average_daily_dosage'),
            User.full_name.label('most_common_doctor')
        ).join(
            PatientMedication, Medication.id == PatientMedication.medication_id
        ).join(
            User, PatientMedication.assigned_by_doctor == User.id
        ).filter(
            PatientMedication.created_at.between(start_date, end_date)
        ).group_by(Medication.id, Medication.name, Medication.form, User.id, User.full_name)

        # Get top medications by prescription count
        top_meds = query.order_by(func.count(PatientMedication.id).desc()).limit(limit).all()

        result = []
        for row in top_meds:
            result.append(TopPrescribedMedications(
                medication_id=row.medication_id,
                medication_name=row.medication_name,
                form=row.form.value if row.form else 'unknown',
                prescriptions_count=row.prescriptions_count or 0,
                unique_patients=row.unique_patients or 0,
                average_daily_dosage=round(float(row.average_daily_dosage or 0), 1),
                most_common_doctor=row.most_common_doctor
            ))

        return result

    @staticmethod
    def get_medication_analytics_summary(db: Session) -> MedicationAnalyticsSummary:
        """Get comprehensive medication analytics summary"""

        # Get usage stats for last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        usage_stats = MedicationAnalyticsService.get_medication_usage_stats(db, start_date, end_date)

        status_distribution = MedicationAnalyticsService.get_medication_status_distribution(db)
        top_medications = MedicationAnalyticsService.get_medication_popularity(db, 10)

        # Recent activity (placeholder)
        recent_activity = {
            "new_medications_added": 3,
            "prescriptions_today": 12,
            "medications_discontinued": 2
        }

        # Prescription trends (placeholder - simplified)
        prescription_trends = {
            "daily": [5, 8, 12, 15, 10, 14, 18],
            "weekly": [45, 52, 48, 61]
        }

        return MedicationAnalyticsSummary(
            usage_stats=usage_stats,
            status_distribution=status_distribution,
            top_medications=top_medications,
            recent_activity=recent_activity,
            prescription_trends=prescription_trends
        )