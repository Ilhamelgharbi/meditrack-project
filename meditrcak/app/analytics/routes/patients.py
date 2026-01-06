"""
Patient analytics routes
Provides analytics for patient management and demographics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.database.db import get_db
from app.analytics.schemas.patients import (
    PatientDemographics,
    PatientStatusDistribution,
    PatientRegistrationTrend,
    PatientHealthMetrics,
    PatientAnalyticsSummary
)
from app.analytics.services.patients import PatientAnalyticsService
from app.auth.services import require_admin
from app.auth.models import User

router = APIRouter()


@router.get("/demographics", response_model=PatientDemographics)
async def get_patient_demographics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get patient demographic statistics"""
    return PatientAnalyticsService.get_patient_demographics(db)


@router.get("/status-distribution", response_model=PatientStatusDistribution)
async def get_patient_status_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get distribution of patients by health status"""
    return PatientAnalyticsService.get_patient_status_distribution(db)


@router.get("/registration-trends", response_model=List[PatientRegistrationTrend])
async def get_patient_registration_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    days: int = Query(90, description="Number of days to analyze", ge=7, le=365)
):
    """Get patient registration trends over time"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    return PatientAnalyticsService.get_patient_registration_trends(db, start_date, end_date)


@router.get("/health-metrics", response_model=PatientHealthMetrics)
async def get_patient_health_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get patient health metrics and statistics"""
    return PatientAnalyticsService.get_patient_health_metrics(db)


@router.get("/summary", response_model=PatientAnalyticsSummary)
async def get_patient_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive patient analytics summary"""
    return PatientAnalyticsService.get_patient_analytics_summary(db)