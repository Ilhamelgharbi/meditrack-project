# app/agent/tools/patients/adherence_tools.py
"""
Patient Tools for Adherence Tracking.

Mirrors React adherence features:
- View personal adherence statistics
- Track adherence trends and goals
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.database.db import get_db
from app.adherence.services import AdherenceService
import logging

logger = logging.getLogger(__name__)


class Context(TypedDict):
    """Context passed to tools from the agent runtime."""
    user_id: str
    token: str
    role: str


def _get_db_session() -> Session:
    """Get a database session."""
    return next(get_db())


# ============================================================================
# PATIENT ADHERENCE TOOLS
# ============================================================================

@tool("get_my_adherence_stats", description="Get my medication adherence statistics for a time period.")
def get_my_adherence_stats(
    runtime: ToolRuntime[Context],
    period: str = "weekly"
) -> str:
    """
    Get my medication adherence statistics.

    Args:
        period: Time period ('daily', 'weekly', 'monthly', 'overall')

    Returns:
        Adherence statistics and metrics
    """
    try:
        user_id = int(runtime.config["configurable"]["user_id"])
        db: Session = next(get_db())

        # Use the AdherenceService to get stats
        stats = AdherenceService.get_adherence_stats(db, user_id, period)

        if not stats:
            return f"No adherence data available for the {period} period."

        response = f"""Adherence Statistics ({period}):
- Total doses scheduled: {stats.total_scheduled}
- Doses taken: {stats.total_taken}
- Doses skipped: {stats.total_skipped}
- Doses missed: {stats.total_missed}
- Overall adherence rate: {stats.adherence_score:.1f}%
- On-time adherence rate: {stats.on_time_score:.1f}%
- Current streak: {stats.current_streak} days
- Longest streak: {stats.longest_streak} days"""

        logger.info(f"Adherence stats retrieved for user {user_id}: {stats.adherence_score:.1f}% adherence")
        return response

    except Exception as e:
        logger.error(f"Error getting adherence stats for user {runtime.config.get('configurable', {}).get('user_id', 'unknown')}: {str(e)}")
        return f"Error retrieving adherence statistics: {str(e)}"
    finally:
        db.close()


@tool("get_adherence_trends", description="Get adherence trends over time.")
def get_adherence_trends(
    runtime: ToolRuntime[Context],
    days: int = 30
) -> str:
    """
    Get adherence trends and patterns over time.

    Args:
        days: Number of days to analyze

    Returns:
        Adherence trends and insights
    """
    # TODO: Implement adherence trends analysis
    return f"Patient adherence trends tool - placeholder for {days} days"


@tool("get_adherence_goals", description="Get my current adherence goals and targets.")
def get_adherence_goals(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get my adherence goals and targets.

    Returns:
        Current adherence goals and progress
    """
    # TODO: Implement adherence goals retrieval
    return "Patient adherence goals tool - placeholder implementation"


@tool("get_adherence_insights", description="Get AI-powered insights about my adherence patterns.")
def get_adherence_insights(
    runtime: ToolRuntime[Context]
) -> str:
    """
    Get personalized insights about adherence patterns and suggestions.

    Returns:
        AI-generated insights and recommendations
    """
    # TODO: Implement adherence insights generation
    return "Patient adherence insights tool - placeholder implementation"


@tool("export_adherence_report", description="Generate and export an adherence report.")
def export_adherence_report(
    runtime: ToolRuntime[Context],
    period: str = "monthly",
    format: str = "text"
) -> str:
    """
    Generate a comprehensive adherence report.

    Args:
        period: Time period for the report
        format: Export format ('text', 'csv', 'pdf')

    Returns:
        Adherence report in specified format
    """
    # TODO: Implement adherence report generation
    return f"Patient adherence report tool - placeholder for period '{period}', format '{format}'"