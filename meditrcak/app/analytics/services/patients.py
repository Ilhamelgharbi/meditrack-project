"""
Patient analytics service
Provides analytics calculations for patient management and demographics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case
from typing import List
from datetime import date, timedelta

from app.analytics.schemas.patients import (
    PatientDemographics,
    PatientStatusDistribution,
    PatientRegistrationTrend,
    PatientHealthMetrics,
    PatientAnalyticsSummary
)
from app.patients.models import Patient, GenderEnum, StatusEnum
from app.auth.models import User


class PatientAnalyticsService:
    """Service for calculating patient analytics"""

    @staticmethod
    def get_patient_demographics(db: Session) -> PatientDemographics:
        """Calculate patient demographic statistics"""

        # Total patients
        total_patients = db.query(func.count(Patient.id)).scalar() or 0

        # Gender distribution
        gender_stats = db.query(
            Patient.gender,
            func.count(Patient.id).label('count')
        ).group_by(Patient.gender).all()

        gender_distribution = {}
        for gender, count in gender_stats:
            if gender:
                gender_distribution[gender.value] = count
            else:
                gender_distribution['unknown'] = count

        # Age distribution (SQLite compatible)
        today = date.today()
        age_stats = db.query(
            case(
                ((func.julianday(today) - func.julianday(Patient.date_of_birth)) / 365.25 < 18, 'under_18'),
                ((func.julianday(today) - func.julianday(Patient.date_of_birth)) / 365.25 < 30, '18_29'),
                ((func.julianday(today) - func.julianday(Patient.date_of_birth)) / 365.25 < 50, '30_49'),
                ((func.julianday(today) - func.julianday(Patient.date_of_birth)) / 365.25 < 70, '50_69'),
                else_='70_plus'
            ).label('age_group'),
            func.count(Patient.id).label('count')
        ).filter(Patient.date_of_birth.isnot(None)).group_by('age_group').all()

        age_distribution = {}
        for age_group, count in age_stats:
            age_distribution[age_group or 'unknown'] = count

        # Average age (SQLite compatible)
        today = date.today()
        avg_age_result = db.query(func.avg((func.julianday(today) - func.julianday(Patient.date_of_birth)) / 365.25)).filter(
            Patient.date_of_birth.isnot(None)
        ).scalar()
        average_age = float(avg_age_result) if avg_age_result else None

        # Blood type distribution
        blood_stats = db.query(
            Patient.blood_type,
            func.count(Patient.id).label('count')
        ).filter(Patient.blood_type.isnot(None)).group_by(Patient.blood_type).all()

        blood_type_distribution = {}
        for blood_type, count in blood_stats:
            blood_type_distribution[blood_type] = count

        # Registration trend (simplified - last 12 months)
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        registration_stats = db.query(
            func.strftime('%Y-%m', User.date_created).label('month'),
            func.count(User.id).label('count')
        ).join(
            Patient, User.id == Patient.user_id
        ).filter(
            User.date_created.between(start_date, end_date)
        ).group_by(func.strftime('%Y-%m', User.date_created)).order_by('month').all()

        registration_trend = {}
        for month, count in registration_stats:
            month_str = month if isinstance(month, str) else str(month)
            registration_trend[month_str] = count

        return PatientDemographics(
            total_patients=total_patients,
            gender_distribution=gender_distribution,
            age_distribution=age_distribution,
            average_age=round(average_age, 1) if average_age else None,
            blood_type_distribution=blood_type_distribution,
            registration_trend=registration_trend
        )

    @staticmethod
    def get_patient_status_distribution(db: Session) -> PatientStatusDistribution:
        """Get distribution of patients by health status"""

        status_stats = db.query(
            Patient.status,
            func.count(Patient.id).label('count')
        ).group_by(Patient.status).all()

        status_counts = {'stable': 0, 'critical': 0, 'under_observation': 0}
        total = 0

        for status, count in status_stats:
            if status:
                status_counts[status.value] = count
            total += count

        status_percentages = {}
        for status, count in status_counts.items():
            status_percentages[status] = round((count / total * 100), 1) if total > 0 else 0

        return PatientStatusDistribution(
            stable=status_counts['stable'],
            critical=status_counts['critical'],
            under_observation=status_counts['under_observation'],
            total_patients=total,
            status_percentages=status_percentages
        )

    @staticmethod
    def get_patient_registration_trends(db: Session, start_date: date, end_date: date) -> List[PatientRegistrationTrend]:
        """Get patient registration trends over time"""

        # Get daily registration counts
        daily_stats = db.query(
            func.date(User.date_created).label('registration_date'),
            func.count(User.id).label('new_registrations')
        ).join(
            Patient, User.id == Patient.user_id
        ).filter(
            User.date_created.between(start_date, end_date)
        ).group_by(func.date(User.date_created)).order_by('registration_date').all()

        # Calculate cumulative totals
        trends = []
        cumulative_total = 0

        for reg_date, new_count in daily_stats:
            cumulative_total += new_count
            trends.append(PatientRegistrationTrend(
                date=reg_date,
                new_registrations=new_count,
                cumulative_total=cumulative_total
            ))

        return trends

    @staticmethod
    def get_patient_health_metrics(db: Session) -> PatientHealthMetrics:
        """Get patient health metrics and statistics"""

        # BMI calculations (BMI = weight_kg / (height_m)^2)
        bmi_stats = db.query(
            (Patient.weight / ((Patient.height / 100) * (Patient.height / 100))).label('bmi')
        ).filter(
            Patient.weight.isnot(None),
            Patient.height.isnot(None),
            Patient.height > 0
        ).all()

        bmis = [bmi[0] for bmi in bmi_stats if bmi[0]]
        average_bmi = sum(bmis) / len(bmis) if bmis else None

        # BMI distribution
        bmi_distribution = {'underweight': 0, 'normal': 0, 'overweight': 0, 'obese': 0}
        for bmi in bmis:
            if bmi < 18.5:
                bmi_distribution['underweight'] += 1
            elif bmi < 25:
                bmi_distribution['normal'] += 1
            elif bmi < 30:
                bmi_distribution['overweight'] += 1
            else:
                bmi_distribution['obese'] += 1

        # Allergies
        patients_with_allergies = db.query(func.count(Patient.id)).filter(
            Patient.allergies.isnot(None),
            Patient.allergies != ''
        ).scalar() or 0

        # Common allergies (simplified - would need text analysis)
        common_allergies = [
            {"allergen": "Penicillin", "count": 15},
            {"allergen": "Sulfa drugs", "count": 8},
            {"allergen": "Nuts", "count": 12}
        ]  # Placeholder data

        # Height and weight averages
        height_stats = db.query(func.avg(Patient.height)).filter(Patient.height.isnot(None)).scalar()
        weight_stats = db.query(func.avg(Patient.weight)).filter(Patient.weight.isnot(None)).scalar()

        average_height = float(height_stats) if height_stats else None
        average_weight = float(weight_stats) if weight_stats else None

        # Medical history
        patients_with_medical_history = db.query(func.count(Patient.id)).filter(
            Patient.medical_history.isnot(None),
            Patient.medical_history != ''
        ).scalar() or 0

        return PatientHealthMetrics(
            average_bmi=round(average_bmi, 1) if average_bmi else None,
            bmi_distribution=bmi_distribution,
            patients_with_allergies=patients_with_allergies,
            common_allergies=common_allergies,
            average_height=round(average_height, 1) if average_height else None,
            average_weight=round(average_weight, 1) if average_weight else None,
            patients_with_medical_history=patients_with_medical_history
        )

    @staticmethod
    def get_patient_analytics_summary(db: Session) -> PatientAnalyticsSummary:
        """Get comprehensive patient analytics summary"""

        demographics = PatientAnalyticsService.get_patient_demographics(db)
        status_distribution = PatientAnalyticsService.get_patient_status_distribution(db)
        health_metrics = PatientAnalyticsService.get_patient_health_metrics(db)

        # Recent activity (placeholder)
        recent_activity = {
            "new_registrations_last_7_days": 5,
            "active_patients_today": 45,
            "patients_with_appointments": 12
        }

        # Admin workload (placeholder)
        admin_workload = {
            "patients_per_admin_avg": 8,
            "admins_with_overload": 2
        }

        return PatientAnalyticsSummary(
            demographics=demographics,
            status_distribution=status_distribution,
            health_metrics=health_metrics,
            recent_activity=recent_activity,
            admin_workload=admin_workload
        )