"""
Analytics module for healthcare management system
Provides analytics and reporting functionality for patients, medications, and adherence
"""

from fastapi import APIRouter

from .routes import adherence, patients, medications, html_routes

# Create main analytics router
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Include sub-routers
router.include_router(adherence.router, prefix="/adherence", tags=["adherence-analytics"])
router.include_router(patients.router, prefix="/patients", tags=["patient-analytics"])
router.include_router(medications.router, prefix="/medications", tags=["medication-analytics"])
router.include_router(html_routes.router, tags=["analytics-html"])