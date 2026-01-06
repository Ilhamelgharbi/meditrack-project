"""
Medication analytics routes
Provides analytics for medication usage and management
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.database.db import get_db
from app.analytics.schemas.medications import (
    MedicationUsageStats,
    MedicationPopularity,
    MedicationStatusDistribution,
    MedicationAnalyticsSummary,
    TopPrescribedMedications
)
from app.analytics.services.medications import MedicationAnalyticsService
from app.auth.services import require_admin
from app.auth.models import User

router = APIRouter()


@router.get("/usage-stats", response_model=MedicationUsageStats)
async def get_medication_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis")
):
    """Get overall medication usage statistics"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    return MedicationAnalyticsService.get_medication_usage_stats(db, start_date, end_date)


@router.get("/popularity", response_model=List[MedicationPopularity])
async def get_medication_popularity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = Query(20, description="Number of medications to return", ge=1, le=100),
    min_prescriptions: Optional[int] = Query(None, description="Minimum number of prescriptions")
):
    """Get most popular medications by prescription count"""
    return MedicationAnalyticsService.get_medication_popularity(db, limit, min_prescriptions)


@router.get("/status-distribution", response_model=MedicationStatusDistribution)
async def get_medication_status_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get distribution of medications by status (active, pending, stopped)"""
    return MedicationAnalyticsService.get_medication_status_distribution(db)


@router.get("/top-prescribed", response_model=List[TopPrescribedMedications])
async def get_top_prescribed_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    limit: int = Query(10, description="Number of medications to return", ge=1, le=50)
):
    """Get top prescribed medications in the specified period"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    return MedicationAnalyticsService.get_top_prescribed_medications(db, start_date, end_date, limit)


@router.get("/summary", response_model=MedicationAnalyticsSummary)
async def get_medication_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive medication analytics summary"""
    return MedicationAnalyticsService.get_medication_analytics_summary(db)