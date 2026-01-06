from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.auth.services import get_current_user
from app.auth.models import User, RoleEnum
from app.adherence.services import AdherenceService
from app.adherence.schemas import (
    MedicationLogCreate, MedicationLogUpdate, MedicationLogResponse,
    AdherenceStatsResponse, AdherenceChartData, AdherenceDashboard
)

router = APIRouter(prefix="/adherence", tags=["Adherence"])


# ==================== MEDICATION LOG ROUTES ====================

@router.post("/logs", response_model=MedicationLogResponse, status_code=status.HTTP_201_CREATED)
def log_medication(
    log_data: MedicationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a medication dose (taken, skipped, or missed)
    Patient can only log their own medications
    """
    return AdherenceService.log_medication(db, log_data, current_user.id)


@router.put("/logs/{log_id}", response_model=MedicationLogResponse)
def update_medication_log(
    log_id: int,
    log_data: MedicationLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing medication log
    Patient can only update their own logs
    """
    return AdherenceService.update_medication_log(db, log_id, log_data, current_user.id)


@router.get("/logs", response_model=List[MedicationLogResponse])
def get_medication_logs(
    patient_medication_id: Optional[int] = Query(None, description="Filter by specific medication assignment"),
    status: Optional[str] = Query(None, description="Filter by status: taken, skipped, missed"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get medication logs for current patient
    Can filter by medication, status, and date range
    """
    from datetime import date as date_type
    
    # Convert string dates to date objects if provided
    start_date_obj = date_type.fromisoformat(start_date) if start_date else None
    end_date_obj = date_type.fromisoformat(end_date) if end_date else None
    
    return AdherenceService.get_patient_logs(
        db,
        patient_id=current_user.id,
        patient_medication_id=patient_medication_id,
        status_filter=status,
        start_date=start_date_obj,
        end_date=end_date_obj,
        skip=skip,
        limit=limit
    )


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a medication log
    Patient can only delete their own logs
    """
    AdherenceService.delete_medication_log(db, log_id, current_user.id)
    return None


# ==================== ADHERENCE STATS ROUTES ====================

@router.get("/stats", response_model=AdherenceStatsResponse)
def get_adherence_stats(
    period: str = Query("weekly", description="Period: daily, weekly, monthly, overall"),
    patient_medication_id: Optional[int] = Query(None, description="Filter by specific medication"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adherence statistics for current patient
    Calculates adherence score, streaks, on-time percentage
    """
    if period not in ["daily", "weekly", "monthly", "overall"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be one of: daily, weekly, monthly, overall"
        )
    
    return AdherenceService.get_adherence_stats(
        db,
        patient_id=current_user.id,
        period_type=period,
        patient_medication_id=patient_medication_id
    )


@router.get("/chart", response_model=List[AdherenceChartData])
def get_adherence_chart_data(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    patient_medication_id: Optional[int] = Query(None, description="Filter by specific medication"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adherence chart data for visualization
    Returns daily adherence scores for the specified period
    """
    return AdherenceService.get_chart_data(
        db,
        patient_id=current_user.id,
        days=days
    )


@router.get("/dashboard", response_model=AdherenceDashboard)
def get_adherence_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete adherence dashboard with all stats and recent logs
    Includes overall, weekly, and daily stats plus chart data
    """
    return AdherenceService.get_dashboard(db, current_user.id)


# ==================== ADMIN ROUTES ====================

@router.get("/patients/{patient_id}/stats", response_model=AdherenceStatsResponse)
def get_patient_adherence_stats(
    patient_id: int,
    period: str = Query("weekly", description="Period: daily, weekly, monthly, overall"),
    patient_medication_id: Optional[int] = Query(None, description="Filter by specific medication"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adherence statistics for a specific patient (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view other patients' adherence stats"
        )
    
    if period not in ["daily", "weekly", "monthly", "overall"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be one of: daily, weekly, monthly, overall"
        )
    
    return AdherenceService.get_adherence_stats(
        db,
        patient_id=patient_id,
        period_type=period,
        patient_medication_id=patient_medication_id
    )


@router.get("/patients/{patient_id}/logs", response_model=List[MedicationLogResponse])
def get_patient_logs_admin(
    patient_id: int,
    patient_medication_id: Optional[int] = Query(None, description="Filter by specific medication assignment"),
    status: Optional[str] = Query(None, description="Filter by status: taken, skipped, missed"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get medication logs for a specific patient (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view other patients' logs"
        )
    
    from datetime import date as date_type
    
    # Convert string dates to date objects if provided
    start_date_obj = date_type.fromisoformat(start_date) if start_date else None
    end_date_obj = date_type.fromisoformat(end_date) if end_date else None
    
    return AdherenceService.get_patient_logs(
        db,
        patient_id=patient_id,
        patient_medication_id=patient_medication_id,
        status_filter=status,
        start_date=start_date_obj,
        end_date=end_date_obj,
        skip=skip,
        limit=limit
    )


@router.get("/patients/{patient_id}/dashboard", response_model=AdherenceDashboard)
def get_patient_dashboard_admin(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete adherence dashboard for a specific patient (Admin only)
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view other patients' dashboards"
        )
    
    return AdherenceService.get_dashboard(db, patient_id)
