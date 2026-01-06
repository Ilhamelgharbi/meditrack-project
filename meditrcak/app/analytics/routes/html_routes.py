"""
HTML Analytics routes
Provides web interface for viewing analytics data
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.database.db import get_db
from app.analytics.services.adherence import AdherenceAnalyticsService
from app.analytics.services.patients import PatientAnalyticsService
from app.analytics.services.medications import MedicationAnalyticsService
from app.auth.services import require_admin
from app.auth.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/test")
async def test_html():
    """Simple test HTML route"""
    return {"message": "HTML routes are working", "test": True}


@router.get("/dashboard")
async def analytics_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    # current_user: User = Depends(require_admin)  # Temporarily disabled for testing
):
    """Analytics dashboard HTML view"""
    # Get current date info
    today = date.today()
    start_date = today - timedelta(days=30)

    # Gather all analytics data
    adherence_overview = AdherenceAnalyticsService.get_adherence_overview(db, start_date, today)
    adherence_trends = AdherenceAnalyticsService.get_adherence_trends(db, start_date, today, None)[:14]  # Last 14 days
    patient_status = PatientAnalyticsService.get_patient_status_distribution(db)
    medication_status = MedicationAnalyticsService.get_medication_status_distribution(db)
    top_patients = AdherenceAnalyticsService.get_patient_adherence_summary(db, 10, None)[:5]  # Top 5

    # Calculate overview metrics
    overview = {
        "total_patients": len(PatientAnalyticsService.get_patient_analytics_summary(db).get("active_patients", 0)) if hasattr(PatientAnalyticsService.get_patient_analytics_summary(db), "get") else 0,
        "total_medications": len(MedicationAnalyticsService.get_medication_analytics_summary(db).get("total_unique_medications", 0)) if hasattr(MedicationAnalyticsService.get_medication_analytics_summary(db), "get") else 0,
        "average_adherence": adherence_overview.average_adherence_rate if hasattr(adherence_overview, "average_adherence_rate") else 0,
        "total_doses_today": sum(trend.doses_scheduled for trend in adherence_trends[-1:]) if adherence_trends else 0
    }

    # Get actual patient and medication counts
    try:
        patient_summary = PatientAnalyticsService.get_patient_analytics_summary(db)
        overview["total_patients"] = patient_summary.active_patients if hasattr(patient_summary, "active_patients") else 0
    except:
        overview["total_patients"] = 0

    try:
        medication_summary = MedicationAnalyticsService.get_medication_analytics_summary(db)
        overview["total_medications"] = medication_summary.total_unique_medications if hasattr(medication_summary, "total_unique_medications") else 0
    except:
        overview["total_medications"] = 0

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "overview": overview,
        "trends": adherence_trends,
        "patient_status": patient_status,
        "medication_status": medication_status,
        "top_patients": top_patients,
        "current_time": today,
        "start_date": start_date,
        "end_date": today
    })


@router.get("/adherence")
async def adherence_analytics_html(
    request: Request,
    db: Session = Depends(get_db),
    # current_user: User = Depends(require_admin),  # Temporarily disabled for testing
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Adherence analytics HTML view"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    overview = AdherenceAnalyticsService.get_adherence_overview(db, start_date, end_date)
    trends = AdherenceAnalyticsService.get_adherence_trends(db, start_date, end_date, None)
    patients = AdherenceAnalyticsService.get_patient_adherence_summary(db, 50, None)
    medications = AdherenceAnalyticsService.get_medication_adherence_details(db, None, 50)
    stats = AdherenceAnalyticsService.get_adherence_stats(db, start_date, end_date, None)

    return templates.TemplateResponse("adherence.html", {
        "request": request,
        "active_page": "adherence",
        "overview": overview,
        "trends": trends,
        "patients": patients,
        "medications": medications,
        "stats": stats
    })


@router.get("/patients")
async def patients_analytics_html(
    request: Request,
    db: Session = Depends(get_db),
    # current_user: User = Depends(require_admin)  # Temporarily disabled for testing
):
    """Patient analytics HTML view"""
    demographics = PatientAnalyticsService.get_patient_demographics(db)
    status_distribution = PatientAnalyticsService.get_patient_status_distribution(db)
    registration_trends = PatientAnalyticsService.get_patient_registration_trends(db, date.today() - timedelta(days=90), date.today())
    health_metrics = PatientAnalyticsService.get_patient_health_metrics(db)
    summary = PatientAnalyticsService.get_patient_analytics_summary(db)

    # Mock age distribution for now (would need to implement in service)
    age_distribution = [
        {"age_group": "18-30", "count": 15, "percentage": 25.0, "average_bmi": 22.5},
        {"age_group": "31-50", "count": 25, "percentage": 41.7, "average_bmi": 24.8},
        {"age_group": "51-70", "count": 18, "percentage": 30.0, "average_bmi": 26.2},
        {"age_group": "70+", "count": 2, "percentage": 3.3, "average_bmi": 25.1}
    ]

    return templates.TemplateResponse("patients.html", {
        "request": request,
        "active_page": "patients",
        "demographics": demographics,
        "status_distribution": status_distribution,
        "registration_trends": registration_trends,
        "health_metrics": health_metrics,
        "age_distribution": age_distribution,
        "summary": summary
    })


@router.get("/medications")
async def medications_analytics_html(
    request: Request,
    db: Session = Depends(get_db),
    # current_user: User = Depends(require_admin),  # Temporarily disabled for testing
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Medication analytics HTML view"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    usage_stats = MedicationAnalyticsService.get_medication_usage_stats(db, start_date, end_date)
    popularity = MedicationAnalyticsService.get_medication_popularity(db, 20, None)
    status_distribution = MedicationAnalyticsService.get_medication_status_distribution(db)
    top_prescribed = MedicationAnalyticsService.get_top_prescribed_medications(db, start_date, end_date, 10)
    summary = MedicationAnalyticsService.get_medication_analytics_summary(db)

    return templates.TemplateResponse("medications.html", {
        "request": request,
        "active_page": "medications",
        "usage_stats": usage_stats,
        "popularity": popularity,
        "status_distribution": status_distribution,
        "top_prescribed": top_prescribed,
        "summary": summary
    })