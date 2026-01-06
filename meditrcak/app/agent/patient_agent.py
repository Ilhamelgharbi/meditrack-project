# app/agent/patient_agent.py
"""
Patient Agent - Specialized AI assistant for patients.

Provides patient-specific tools for medication management, reminders, adherence tracking,
and personal health information. Mirrors patient-side React functionality.
"""

import logging
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config.settings import settings
from app.agent.prompt import patient_system_prompt
from langgraph.checkpoint.memory import InMemorySaver
from app.agent.utils.intent_classifier import classify_intent, get_quick_response
from app.agent.tools.patients import (
    # Profile tools
    get_my_profile,
    get_my_vitals,
    update_my_profile,
    update_my_vitals,

    # Medication tools
    get_my_medications,
    get_active_medications,
    get_pending_medications,
    confirm_medication,
    get_inactive_medications,

    # Adherence tools
    get_my_adherence_stats,

    # Reminder tools
    get_my_reminders,
    set_medication_reminder,

    # Medical tools
    get_my_medical_history,
    get_my_allergies,
    get_my_health_summary,

    # Logging tools
    log_medication_taken,
    log_medication_skipped,
    get_recent_medication_logs,
)
from app.agent.tools.image_analysis import analyze_medical_image
from app.agent.tools.pill_identification import identify_pill_complete
from app.agent.rag.vector_store import retrieve_medical_documents
from typing_extensions import TypedDict
from typing import List
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)


# Initialize checkpointer for persistence and memory
from app.agent.memory import get_checkpointer
checkpointer = get_checkpointer(use_persistent=False)  # Use in-memory for now


# Context schema - must be TypedDict as per LangChain v1.0 requirements
class Context(TypedDict):
    """Context schema for patient agent invocations."""
    user_id: str
    token: str
    role: str


# CACHED: System prompt (module-level singleton)
# Optimized for patient interactions with focus on personal health managemen
patient_system_prompt=patient_system_prompt  # Commented out to use local MediTrack AI prompt


# CACHED: LLM Model (module-level singleton)
# Using conservative settings to avoid Groq API rate limits
model = ChatGroq(
    model=settings.GROQ_MODEL_NAME,
    api_key=settings.GROQ_API_KEY,
    temperature=0.1,  # Reduced for faster, more consistent responses
    max_tokens=256,   # Reduced for faster responses and lower rate limit impact
    max_retries=1    # Allow retries but with backoff
)

# Patient Tools - Direct imports (no dynamic loading needed)
# All essential tools are imported directly above

# CACHED: Tools list (module-level singleton)
# Direct import of essential patient tools - no dynamic loading needed
tools = [
    # Profile tools
    get_my_profile,
    get_my_vitals,
    update_my_profile,
    update_my_vitals,

    # Medication tools
    get_my_medications,
    get_active_medications,
    get_pending_medications,
    confirm_medication,
    get_inactive_medications,

    # Adherence tools
    get_my_adherence_stats,

    # Reminder tools
    get_my_reminders,
    set_medication_reminder,

    # Medical tools
    get_my_medical_history,
    get_my_allergies,
    get_my_health_summary,

    # Logging tools
    log_medication_taken,
    log_medication_skipped,
    get_recent_medication_logs,

    # Image analysis and pill identification tools
    analyze_medical_image,
    identify_pill_complete,

    # Medical knowledge retrieval (RAG)
    retrieve_medical_documents,
]

def filter_tools_for_query(query: str) -> list:
    """
    Intelligently filter tools based on query content to prevent LLM overload.
    Returns only the most relevant tools for the specific query.
    """
    query_lower = query.lower().strip()

    # Adherence queries (check early as they're specific)
    if any(word in query_lower for word in ["adherence", "compliance", "streak", "progress", "following", "sticking", "properly", "rate", "how well", "how am i"]):
        return [get_my_adherence_stats]

    # Reminder queries (check before action-based to avoid conflicts)
    if any(word in query_lower for word in ["reminder", "reminders", "alerts", "notifications", "schedule"]) and not any(word in query_lower for word in ["set", "create", "add"]):
        return [get_my_reminders, set_medication_reminder]
    if any(word in query_lower for word in ["update", "change", "modify", "edit"]) and any(word in query_lower for word in ["profile", "name", "age", "contact", "personal", "info", "information", "details"]):
        return [update_my_profile]
    if any(word in query_lower for word in ["update", "change", "modify", "edit"]) and any(word in query_lower for word in ["vitals", "blood", "weight", "height", "measurements", "stats", "signs", "health"]):
        return [update_my_vitals]
    if any(word in query_lower for word in ["confirm", "accept", "approve"]) and any(word in query_lower for word in ["medication", "prescription"]):
        return [confirm_medication]
    if any(word in query_lower for word in ["set", "create", "add", "remind"]) and any(word in query_lower for word in ["reminder", "reminders", "alert", "notification", "schedule", "prescription", "medication", "pill", "medicine"]):
        return [set_medication_reminder]
    if any(word in query_lower for word in ["took", "taken", "consumed", "ingested", "had", "skip", "skipped", "forgot", "missed", "didn't take"]) and any(word in query_lower for word in ["medication", "medications", "pill", "pills", "medicine", "drug", "drugs", "dose"]):
        return [log_medication_taken, log_medication_skipped, get_recent_medication_logs]

    # General medication queries (moved up to prevent conflicts with pill identification)
    if any(word in query_lower for word in ["medication", "medications", "pills", "prescription", "drugs", "medicines"]) and not any(word in query_lower for word in ["pending", "stopped", "inactive", "discontinued", "quit", "log", "logs", "history", "activity", "recent", "display", "schedule"]):
        return [get_active_medications]

    # Pill identification (check after general medication queries to avoid conflicts)
    if any(word in query_lower for word in ["identify", "recognize", "find out", "what is", "what kind", "tell me what"]) and any(word in query_lower for word in ["pill", "tablet", "medicine", "medication"]):
        return [identify_pill_complete]

    # Image analysis (check before medical queries to avoid "medical" matching)
    if any(word in query_lower for word in ["analyze", "examine", "check", "look", "image", "photo", "picture", "scan"]):
        return [analyze_medical_image]

    # Exact matches for common queries
    if query_lower in ["what medications do i take", "what medications do i take?", "medications i take"]:
        return [get_active_medications]
    if query_lower in ["what is my health summary", "give me a health summary"]:
        return [get_my_health_summary]
    if query_lower == "what is my medical history":
        return [get_my_medical_history]
    if query_lower == "what allergies do i have":
        return [get_my_allergies]
    if query_lower == "please identify this pill from the image":
        return [identify_pill_complete]

    # Specific medication queries
    if ("pending" in query_lower or "waiting" in query_lower) and any(word in query_lower for word in ["medication", "medications", "prescription", "drug", "drugs"]):
        return [get_pending_medications, confirm_medication]
    if ("stopped" in query_lower or "inactive" in query_lower or "discontinued" in query_lower or "quit" in query_lower or "stop taking" in query_lower) and any(word in query_lower for word in ["medication", "medications", "drug", "drugs", "pill", "pills"]):
        return [get_inactive_medications]

    # Medication logging queries (check before medical history to avoid conflicts)
    if any(word in query_lower for word in ["log", "logs", "activity", "recent", "display", "history"]) and any(word in query_lower for word in ["medication", "medications", "pill", "pills", "medicine"]) and not any(word in query_lower for word in ["medical", "past", "conditions", "background", "health past", "records"]):
        return [log_medication_taken, log_medication_skipped, get_recent_medication_logs]

    # Profile/personal queries
    if any(word in query_lower for word in ["profile", "name", "age", "blood", "weight", "height", "vitals", "measurements", "stats", "signs", "personal", "info", "information", "details", "about myself"]):
        return [get_my_profile, get_my_vitals]

    # Medical history queries
    if any(word in query_lower for word in ["medical", "history", "records", "past", "conditions", "background", "health past"]) and not any(word in query_lower for word in ["medication", "medications", "pill", "pills", "medicine", "log", "logs", "activity", "recent", "display"]):
        return [get_my_medical_history, get_my_health_summary]

    # Allergy queries
    if any(word in query_lower for word in ["allerg", "reaction", "sensitiv", "substance", "bother"]):
        return [get_my_allergies]

    # Health summary queries
    if any(word in query_lower for word in ["summary", "overview", "status", "overall health", "medical condition"]):
        return [get_my_health_summary]

    # General medical knowledge (fallback for medical questions - check this last)
    if any(word in query_lower for word in ["what is", "how does", "how is", "explain", "tell me about", "side effects", "causes", "symptoms", "treatment", "treated", "work", "works"]) and not any(word in query_lower for word in ["my", "I", "profile", "vitals", "reminder", "history", "allergy", "summary"]):
        return [retrieve_medical_documents]

    # Default: use all tools for maximum flexibility (best practice)
    # This ensures the agent can handle any query by having access to all capabilities
    return tools

def clear_agent_cache():
    """Clear the agent cache to force recreation with updated tools/prompts."""
    # No-op since we don't use caching anymore
    logger.info("Agent cache clearing not needed (no caching implemented)")


def ask_patient_agent(messages: list, user_context: dict = None) -> dict:
    """
    Send messages to the patient AI agent and get the response.

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
    logger.debug(f"Patient agent - Classified intent: {intent} for message: '{last_message[:50]}...'")

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
        logger.info(f"Patient agent - Quick response for {intent}: {len(response)} chars (no tools called)")
        return {
            "response": response,
            "tools_used": [],
            "intent": intent
        }

    # Medical query - proceed with full agent pipeline
    logger.info(f"Patient agent - Processing medical query with agent (user_id: {user_id})")

    # Trim message history to last 10 messages to reduce token usage
    if len(messages) > 10:
        messages = messages[-10:]
        logger.debug("Patient agent - Trimmed message history to last 10 messages")

    # Extract token for authenticated HTTP calls and set it globally
    token = user_context.get("token", "") if user_context else ""

    # Auto-set the token for HTTP-based tools
    if token:
        from app.agent.tools.http_client import set_agent_token, set_agent_user_id
        set_agent_token(token)
        set_agent_user_id(int(user_id))
        logger.debug("Patient agent - JWT token and user_id set for HTTP-based tools")

    # Create context following Context schema
    context = Context(user_id=user_id, token=token, role="patient")

    # Config with thread_id and context - critical for checkpointer and tools
    config = {
        "configurable": {
            "thread_id": f"patient_{user_id}",
            "user_id": user_id,
            "token": token,
            "role": "patient"
        }
    }

    # FILTER TOOLS BASED ON QUERY - prevent calling all tools
    filtered_tools = filter_tools_for_query(last_message)
    logger.info(f"Patient agent - Using filtered tools for query '{last_message[:50]}...': {[getattr(t, 'name', str(t)) for t in filtered_tools]}")

    # Create agent with filtered tools for this query
    agent = create_agent(
        model=model,
        tools=filtered_tools,
        system_prompt=patient_system_prompt,
        checkpointer=checkpointer,
        context_schema=Context,
    )

    # Invoke agent with messages and config
    result = agent.invoke(
        {"messages": messages},
        config=config
    )

    # Extract tools used from the result - only from NEW messages in this turn
    tools_used = []
    # Extract tools used from the result
    for message in result.get("messages", []):
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)

    logger.info(f"Patient agent - Tools used: {tools_used if tools_used else 'None'}")

    # Return response with metadata
    return {
        "response": result["messages"][-1].content,
        "tools_used": tools_used,
        "intent": intent
    }


def ask_patient_agent_streaming(messages: list, user_context: dict = None, stream_mode: str = "values"):
    """
    Send messages to the patient AI agent and stream the response in real-time.

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

        context = {"user_id": user_id, "token": token, "role": "patient"}
        config = {
            "configurable": {
                "thread_id": f"patient_{user_id}",
                "user_id": user_id,
                "token": token,
                "role": "patient"
            }
        }

        # Filter tools for streaming too
        filtered_tools = filter_tools_for_query(messages[-1].content if messages else "")
        streaming_agent = create_agent(
            model=model,
            tools=filtered_tools,
            system_prompt=patient_system_prompt,
            checkpointer=checkpointer,
            context_schema=Context,
        )

        for chunk in streaming_agent.stream(
            {"messages": messages},
            config=config,
            stream_mode=stream_mode
        ):
            yield chunk

    except Exception as e:
        logger.error(f"Error in ask_patient_agent_streaming: {e}", exc_info=True)
        yield {"messages": [AIMessage(content="I'm sorry, I'm experiencing technical difficulties. Please try again later.")], "error": str(e)}
