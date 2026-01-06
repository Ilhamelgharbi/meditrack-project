# app/agent/tools/shared/medication_search_tools.py
"""
Shared Tools for Medication Search and Validation.

Used by both admin and patient tools for medication lookup.
"""

from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.database.db import get_db
from app.medications.models import Medication

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
# SHARED MEDICATION SEARCH TOOLS
# ============================================================================

@tool("search_medications", description="Search for medications in the catalog.")
def search_medications(
    runtime: ToolRuntime[Context],
    query: str,
    limit: int = 10
) -> str:
    """
    Search for medications in the master catalog.

    Args:
        query: Search term for medication names
        limit: Maximum number of results to return

    Returns:
        List of matching medications
    """
    # TODO: Implement medication search
    return f"Shared medication search tool - placeholder for query '{query}', limit {limit}"


@tool("get_medication_suggestions", description="Get autocomplete suggestions for medication names.")
def get_medication_suggestions(
    runtime: ToolRuntime[Context],
    partial_name: str
) -> str:
    """
    Get autocomplete suggestions for medication names.

    Args:
        partial_name: Partial medication name to complete

    Returns:
        List of suggested medication names
    """
    # TODO: Implement medication suggestions
    return f"Shared medication suggestions tool - placeholder for '{partial_name}'"


@tool("validate_medication_name", description="Check if a medication name exists in the catalog.")
def validate_medication_name(
    runtime: ToolRuntime[Context],
    name: str
) -> str:
    """
    Validate if a medication name exists in the catalog.

    Args:
        name: Full medication name to validate

    Returns:
        Validation result and medication details if found
    """
    # TODO: Implement medication name validation
    return f"Shared medication validation tool - placeholder for '{name}'"


@tool("get_similar_medications", description="Find medications similar to a given name.")
def get_similar_medications(
    runtime: ToolRuntime[Context],
    name: str
) -> str:
    """
    Find medications with similar names or ingredients.

    Args:
        name: Medication name to find similar medications for

    Returns:
        List of similar medications
    """
    # TODO: Implement similar medications search
    return f"Shared similar medications tool - placeholder for '{name}'"