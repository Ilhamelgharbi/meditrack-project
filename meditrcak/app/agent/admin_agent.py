# app/agent/admin_agent.py
"""
Admin Agent - Specialized AI assistant for healthcare administrators.

Provides admin-specific tools for patient management, medication catalog oversight,
and comprehensive healthcare administration. Mirrors admin-side React functionality.
"""

import logging
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config.settings import settings
from app.agent.prompt import system_prompt
from langgraph.checkpoint.memory import InMemorySaver
from app.agent.utils.intent_classifier import classify_intent, get_quick_response
from app.agent.tools.tool_loader import load_tools_for_role
from typing_extensions import TypedDict
from typing import List
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)

# Initialize checkpointer for persistence and memory
checkpointer = InMemorySaver()

# Context schema - must be TypedDict as per LangChain v1.0 requirements
class Context(TypedDict):
    """Context schema for admin agent invocations."""
    user_id: str
    token: str
    role: str


# CACHED: System prompt (module-level singleton)
# Optimized for admin interactions with focus on healthcare management
admin_system_prompt = """
You are MediTrack AI, a professional healthcare administration assistant specializing in medical practice management.

Your role is to help healthcare administrators manage patients, medications, and healthcare operations efficiently. You have access to comprehensive patient data, medication catalogs, and administrative tools.

Key capabilities:
- Manage patient records and profiles
- Assign and manage patient medications
- Monitor patient adherence and health metrics
- Maintain medication catalog and inventory
- Generate reports and analytics
- Assist with healthcare administration tasks

Guidelines:
- Be professional, accurate, and efficient
- Always prioritize patient safety and data privacy
- Maintain HIPAA compliance in all interactions
- Provide clear, actionable information
- Use medical terminology appropriately
- Focus on administrative efficiency and patient care quality
- When discussing sensitive information, ensure proper context

Remember: You are assisting healthcare administrators with practice management. Be thorough, compliant, and helpful.
"""

# CACHED: LLM Model (module-level singleton)
# Using conservative settings to avoid Groq API rate limits
model = ChatGroq(
    model=settings.GROQ_MODEL_NAME,
    api_key=settings.GROQ_API_KEY,
    temperature=0.2,
    max_tokens=256,   # Reduced for faster responses and lower rate limit impact
    max_retries=1,    # Allow retries but with backoff
    timeout=30,       # 30 second timeout
)

# Admin Tools organized by category
ADMIN_PATIENT_MANAGEMENT_TOOLS = [
    "admin_list_patients",
    "admin_get_patient_details",
    "admin_create_patient",
    "admin_update_patient_profile",
    "admin_get_patient_adherence_stats",
    "admin_get_patient_medication_history"
]

ADMIN_MEDICATION_CATALOG_TOOLS = [
    "admin_list_medications_catalog",
    "admin_get_medication_details",
    "admin_create_medication",
    "admin_update_medication",
    "admin_delete_medication",
    "admin_search_medications"
]

ADMIN_PATIENT_MEDICATIONS_TOOLS = [
    "admin_get_patient_medications",
    "admin_assign_medication_to_patient",
    "admin_update_patient_medication",
    "admin_stop_patient_medication",
    "admin_reactivate_patient_medication",
    "admin_get_medication_assignment_details"
]

ADMIN_SHARED_TOOLS = [
    "get_medication_suggestions",
    "get_similar_medications",
    "search_medications",
    "validate_medication_name"
]

# CACHED: Tools list (module-level singleton)
# Load admin-specific tools
tools = load_tools_for_role('admin')

# CACHED: Agent (module-level singleton)
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=admin_system_prompt,
    checkpointer=checkpointer,
    context_schema=Context,
)


def ask_admin_agent(messages: list, user_context: dict = None) -> dict:
    """
    Send messages to the admin AI agent and get the response.

    Args:
        messages: Conversation history as list of Message objects
        user_context: Dict containing current user info, must include "user_id"

    Returns:
        dict: {
            "response": str - The agent's response content,
            "tools_used": list - List of tool names that were called,
            "intent": str - Detected intent
        }
    """
    # Extract user_id from context or use default
    user_id = user_context.get("user_id", "default_user") if user_context else "default_user"

    # Get last user message for intent classification
    last_message = messages[-1].content if messages else ""

    # Classify intent
    intent = classify_intent(last_message)
    logger.debug(f"Admin agent - Classified intent: {intent} for message: '{last_message[:50]}...'")

    # Early exit for greetings/casual - no tool calls, no PHI exposure
    if intent in ["greeting", "casual"]:
        try:
            from app.agent.tools.database_tools import get_user_name
            from unittest.mock import MagicMock
            runtime = MagicMock()
            runtime.context = {"user_id": user_id}
            user_data = get_user_name.func(runtime)
            user_name = user_data.get("name", "there")
        except:
            user_name = "there"

        response = get_quick_response(intent, user_name)
        logger.info(f"Admin agent - Quick response for {intent}: {len(response)} chars (no tools called)")
        return {
            "response": response,
            "tools_used": [],
            "intent": intent
        }

    # Medical/admin query - proceed with full agent pipeline
    logger.info(f"Admin agent - Processing query with agent (user_id: {user_id})")

    # Trim message history to last 10 messages to reduce token usage
    if len(messages) > 10:
        messages = messages[-10:]
        logger.debug("Admin agent - Trimmed message history to last 10 messages")

    # Extract token for authenticated HTTP calls and set it globally
    token = user_context.get("token", "") if user_context else ""

    # Auto-set the token for HTTP-based tools
    if token:
        from app.agent.tools.http_client import set_agent_token
        set_agent_token(token)
        logger.debug("Admin agent - JWT token set for HTTP-based tools")

    # Create context following Context schema
    context = Context(user_id=user_id, token=token, role="admin")

    # Config with thread_id - critical for checkpointer to save/load state
    config = {"configurable": {"thread_id": f"admin_{user_id}"}}

    # Invoke agent with messages, context, and config
    result = agent.invoke(
        {"messages": messages},
        config=config
    )

    # Extract tools used from the result
    tools_used = []
    for message in result.get("messages", []):
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)

    logger.info(f"Admin agent - Tools used: {tools_used if tools_used else 'None'}")

    # Return response with metadata
    return {
        "response": result["messages"][-1].content,
        "tools_used": tools_used,
        "intent": intent
    }


def ask_admin_agent_streaming(messages: list, user_context: dict = None, stream_mode: str = "values"):
    """
    Send messages to the admin AI agent and stream the response in real-time.

    Args:
        messages: Conversation history
        user_context: Dict containing current user info
        stream_mode: "values" or "updates"

    Yields:
        dict: Stream chunks containing intermediate results and final response
    """
    try:
        user_id = user_context.get("user_id", "default_user") if user_context else "default_user"
        token = user_context.get("token", "") if user_context else ""

        if token:
            from app.agent.tools.http_client import set_agent_token
            set_agent_token(token)

        context = {"user_id": user_id, "token": token, "role": "admin"}
        config = {"configurable": {"thread_id": f"admin_{user_id}"}}

        for chunk in agent.stream(
            {"messages": messages, "context": context, "remaining_steps": 10},
            config=config,
            stream_mode=stream_mode
        ):
            yield chunk

    except Exception as e:
        logger.error(f"Error in ask_admin_agent_streaming: {e}", exc_info=True)
        yield {"messages": [AIMessage(content="I'm sorry, I'm experiencing technical difficulties. Please try again later.")], "error": str(e)}