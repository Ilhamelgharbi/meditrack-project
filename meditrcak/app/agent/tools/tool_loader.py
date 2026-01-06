# app/agent/tools/tool_loader.py
"""
Tool Loader for Dynamic Agent Tool Management.

Loads tools based on user roles and permissions, mirroring React functionality.
"""

from typing import List, Dict, Any
from langchain_core.tools import Tool
import importlib
import logging

logger = logging.getLogger(__name__)

# Tool modules organized by role
TOOL_MODULES = {
    'admin': [
        'app.agent.tools.admin.patients_tools',
        'app.agent.tools.admin.medications_catalog_tools',
        'app.agent.tools.admin.patient_medications_tools',
    ],
    'patient': [
        'app.agent.tools.patients.profile_tools',
        'app.agent.tools.patients.medication_tools',
        'app.agent.tools.patients.reminder_tools',
        'app.agent.tools.patients.adherence_tools',
        'app.agent.tools.patients.medical_tools',
        'app.agent.tools.patients.logging_tools',
        'app.agent.tools.patients.scheduling_tools',
    ],
    'shared': [
        'app.agent.tools.shared.medication_search_tools',
    ]
}


def load_tools_for_role(user_role: str) -> List[Tool]:
    """
    Load tools appropriate for the user's role.

    Args:
        user_role: User's role ('admin', 'patient', etc.)

    Returns:
        List of LangChain tools for the role
    """
    tools = []

    # Load shared tools (available to all roles)
    tools.extend(_load_module_tools('shared'))

    # Load role-specific tools
    if user_role in TOOL_MODULES:
        tools.extend(_load_module_tools(user_role))

    logger.info(f"Loaded {len(tools)} tools for role '{user_role}'")
    return tools


def _load_module_tools(role: str) -> List[Tool]:
    """
    Load tools from modules for a specific role.

    Args:
        role: Role name ('admin', 'patient', 'shared')

    Returns:
        List of tools from the role's modules
    """
    tools = []

    for module_name in TOOL_MODULES[role]:
        try:
            module = importlib.import_module(module_name)

            # Find all tool functions in the module
            # Tools are identified by having a 'func' attribute (LangChain @tool decorator adds this)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, 'func') and hasattr(attr, 'name'):
                    tools.append(attr)

        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error loading tools from {module_name}: {e}")

    return tools


def get_available_tool_names(user_role: str) -> List[str]:
    """
    Get names of available tools for a role.

    Args:
        user_role: User's role

    Returns:
        List of tool names
    """
    tools = load_tools_for_role(user_role)
    return [tool.name for tool in tools]


def get_tool_descriptions(user_role: str) -> Dict[str, str]:
    """
    Get descriptions of available tools for a role.

    Args:
        user_role: User's role

    Returns:
        Dictionary mapping tool names to descriptions
    """
    tools = load_tools_for_role(user_role)
    return {tool.name: tool.description for tool in tools}


# ============================================================================
# REACT FUNCTIONALITY MAPPING
# ============================================================================

REACT_TO_AGENT_MAPPING = {
    # Admin Tools Mapping
    'admin/patients': [
        'admin_list_patients',
        'admin_get_patient_details',
        'admin_update_patient_profile',
        'admin_create_patient',
        'admin_get_patient_adherence_stats',
        'admin_get_patient_medication_history'
    ],
    'admin/medications': [
        'admin_list_medications_catalog',
        'admin_get_medication_details',
        'admin_create_medication',
        'admin_update_medication',
        'admin_delete_medication',
        'admin_search_medications'
    ],
    'admin/patient-medications': [
        'admin_get_patient_medications',
        'admin_assign_medication_to_patient',
        'admin_update_patient_medication',
        'admin_stop_patient_medication',
        'admin_reactivate_patient_medication',
        'admin_get_medication_assignment_details'
    ],

    # Patient Tools Mapping
    'patient/profile': [
        'get_my_profile',
        'update_my_profile',
        'get_my_vitals',
        'update_my_vitals'
    ],
    'patient/medications': [
        'get_my_medications',
        'get_medication_details',
        'accept_medication',
        'get_pending_medications',
        'get_active_medications',
        'log_medication_action'
    ],
    'patient/reminders': [
        'get_my_reminders',
        'get_upcoming_reminders',
        'snooze_reminder',
        'complete_reminder',
        'get_reminder_history'
    ],
    'patient/adherence': [
        'get_my_adherence_stats',
        'get_adherence_trends',
        'get_adherence_goals',
        'get_adherence_insights',
        'export_adherence_report'
    ],
    'patient/scheduling': [
        'get_my_schedule',
        'create_medication_schedule',
        'update_medication_schedule',
        'delete_medication_schedule',
        'get_weekly_schedule',
        'reschedule_medication',
        'get_schedule_conflicts',
        'optimize_schedule'
    ],

    # Shared Tools
    'shared/search': [
        'search_medications',
        'get_medication_suggestions',
        'validate_medication_name',
        'get_similar_medications'
    ]
}


def get_tools_for_react_component(component: str, user_role: str) -> List[Tool]:
    """
    Get tools that correspond to a specific React component.

    Args:
        component: React component name (e.g., 'admin/patients', 'patient/medications')
        user_role: User's role to ensure proper access

    Returns:
        List of relevant tools for the component
    """
    if component not in REACT_TO_AGENT_MAPPING:
        logger.warning(f"No tool mapping found for component: {component}")
        return []

    tool_names = REACT_TO_AGENT_MAPPING[component]
    all_tools = load_tools_for_role(user_role)

    # Filter tools by the mapped names
    component_tools = [tool for tool in all_tools if tool.name in tool_names]

    logger.info(f"Loaded {len(component_tools)} tools for component '{component}'")
    return component_tools