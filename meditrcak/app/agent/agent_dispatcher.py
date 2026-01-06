# app/agent/agent_dispatcher.py
"""
Agent Dispatcher - Routes requests to appropriate specialized agents based on user role.

Provides a unified interface for patient and admin agents, automatically selecting
the correct agent based on the authenticated user's role.
"""

import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.patient_agent import ask_patient_agent, ask_patient_agent_streaming
from app.agent.admin_agent import ask_admin_agent, ask_admin_agent_streaming

logger = logging.getLogger(__name__)


def ask_agent(messages: list, user_context: dict = None) -> dict:
    """
    Unified agent interface that routes to the appropriate specialized agent.

    Args:
        messages: Conversation history as list of Message objects
        user_context: Dict containing current user info, must include "user_id" and "role"

    Returns:
        dict: {
            "response": str - The agent's response content,
            "tools_used": list - List of tool names that were called,
            "intent": str - Detected intent
        }
    """
    if not user_context:
        logger.warning("No user context provided, using default patient agent")
        return ask_patient_agent(messages, user_context)

    user_role = user_context.get("role", "patient").lower()
    logger.debug(f"Routing to {user_role} agent for user {user_context.get('user_id', 'unknown')}")

    if user_role == "admin":
        return ask_admin_agent(messages, user_context)
    else:
        # Default to patient agent for any non-admin role
        return ask_patient_agent(messages, user_context)


def ask_agent_streaming(messages: list, user_context: dict = None, stream_mode: str = "values"):
    """
    Unified streaming agent interface that routes to the appropriate specialized agent.

    Args:
        messages: Conversation history
        user_context: Dict containing current user info
        stream_mode: "values" or "updates"

    Yields:
        dict: Stream chunks containing intermediate results and final response
    """
    if not user_context:
        logger.warning("No user context provided, using default patient agent")
        yield from ask_patient_agent_streaming(messages, user_context, stream_mode)
        return

    user_role = user_context.get("role", "patient").lower()
    logger.debug(f"Routing streaming to {user_role} agent for user {user_context.get('user_id', 'unknown')}")

    if user_role == "admin":
        yield from ask_admin_agent_streaming(messages, user_context, stream_mode)
    else:
        # Default to patient agent for any non-admin role
        yield from ask_patient_agent_streaming(messages, user_context, stream_mode)


def get_available_tools_for_user(user_role: str) -> List[str]:
    """
    Get the list of available tool names for a specific user role.

    Args:
        user_role: User's role ('patient' or 'admin')

    Returns:
        List of available tool names
    """
    from app.agent.tools.tool_loader import get_available_tool_names

    return get_available_tool_names(user_role)


def get_agent_capabilities(user_role: str) -> Dict[str, Any]:
    """
    Get information about what a specific agent can do.

    Args:
        user_role: User's role ('patient' or 'admin')

    Returns:
        Dict containing agent capabilities and tool descriptions
    """
    from app.agent.tools.tool_loader import get_tool_descriptions

    tool_descriptions = get_tool_descriptions(user_role)

    return {
        "role": user_role,
        "tool_count": len(tool_descriptions),
        "tools": tool_descriptions,
        "capabilities": _get_role_capabilities(user_role)
    }


def _get_role_capabilities(role: str) -> List[str]:
    """Get human-readable capability descriptions for a role."""
    if role.lower() == "admin":
        return [
            "Manage patient records and profiles",
            "Assign and modify patient medications",
            "Monitor patient adherence and health metrics",
            "Maintain medication catalog and inventory",
            "Generate reports and analytics",
            "Assist with healthcare administration tasks"
        ]
    else:  # patient
        return [
            "View and manage personal medications",
            "Accept pending medication prescriptions",
            "Log medication actions (taken, skipped, missed)",
            "View medication reminders and schedules",
            "Track adherence statistics and trends",
            "Access personal health profile information",
            "Receive medication education and reminders"
        ]