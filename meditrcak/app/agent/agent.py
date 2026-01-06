# ai/agent.py
"""
AI Agent module for medical assistant.

Best Practices Applied (from LangChain Official Documentation):
1. Message Handling: Uses proper message state with HumanMessage/AIMessage
2. Memory: Automatic short-term memory via checkpointer + message state
3. Checkpointer: InMemorySaver with proper thread_id configuration
4. Context: TypedDict schema for user context management

Performance Optimizations:
- System prompt: Cached at module level (180 words, optimized)
- LLM model: Cached at module level (ChatGroq instance reused)
- Agent: Cached at module level (single instance for all requests)
- Vector DB: Pre-loaded at rag.vector_store import (HuggingFaceEmbeddings + FAISS)
- Result: Sub-1s response times after initial load
"""

import logging
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agent.tools.database_tools import get_patient_info, get_user_name
from app.agent.rag.vector_store import retrieve_medical_documents
from app.config.settings import settings
from typing_extensions import TypedDict
from app.agent.prompt import system_prompt
from langgraph.checkpoint.memory import InMemorySaver
from app.agent.utils.intent_classifier import classify_intent, get_quick_response
from app.agent.tools.image_analysis import  analyze_medical_image
from app.agent.tools.pill_identification import identify_pill_complete
from app.agent.tools.fda_drug_tool import fda_drug_lookup
from app.agent.tools.medication_tools import (
    list_medications,
    get_medication_details,
    accept_medication,
    log_medication_action,
    list_reminders,
    get_upcoming_doses,
    get_adherence_stats,
    get_medication_history,
    get_medication_dashboard,
)
# from app.agent.memory import get_checkpointer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)

# Initialize checkpointer for persistence and memory
# InMemorySaver: suitable for development; use SqliteSaver or PostgresSaver for production
checkpointer = InMemorySaver()

# Context schema - must be TypedDict as per LangChain v1.0 requirements
class Context(TypedDict):
    """Context schema for agent invocations."""
    user_id: str
    token: str  # JWT token for authenticated HTTP calls to backend APIs



# CACHED: System prompt (module-level singleton)
# Optimized for fast, accurate tool selection with privacy protection
system_prompt = system_prompt
# CACHED: LLM Model (module-level singleton)
# Single ChatGroq instance reused for all requests - optimized for speed
model = ChatGroq(
    model=settings.GROQ_MODEL_NAME,
    api_key=settings.GROQ_API_KEY,
    temperature=0.2,  # Lower for faster, more deterministic responses
    max_tokens=512,  # Reduced to avoid token limits
)

# CACHED: Tools list (module-level singleton)
# Includes database tools, RAG, image analysis, FDA lookup, and medication management
tools = [
    # Core patient info tools (direct DB - for basic queries)
    get_patient_info, 
    get_user_name,
    
    # Medical knowledge retrieval
    retrieve_medical_documents,
    
    # Image analysis tools
    identify_pill_complete, 
    analyze_medical_image,
    
    # FDA drug information
    fda_drug_lookup,
    
    # Medication management tools (HTTP-based - uses JWT auth)
    list_medications,        # Replaces get_user_medications
    get_medication_details,
    accept_medication,
    log_medication_action,
    
    # Reminders and scheduling
    list_reminders,
    get_upcoming_doses,
    
    # Adherence tracking
    get_adherence_stats,
    get_medication_history,
    
    # Dashboard overview
    get_medication_dashboard,
]

# CACHED: Agent (module-level singleton)
# Single agent instance reused for all requests - includes cached model, tools, prompt
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    context_schema=Context,  # Define custom state schema for user context
    # store=memory_store,  # Uncomment for long-term memory across threads
)

def ask_agent(messages: list, user_context: dict = None) -> dict:
    """
    Send messages to the AI agent and get the response.
    
    Implements intent classification for efficient processing:
    - Greetings/casual: Quick response without tool calls
    - Medical queries: Full agent pipeline with tools

    Args:
        messages: Conversation history as list of Message objects (HumanMessage, AIMessage)
                 or dicts with {"role": "user"/"assistant", "content": "..."}
        user_context: Dict containing current user info, must include "user_id"

    Returns:
        dict: {
            "response": str - The agent's response content,
            "tools_used": list - List of tool names that were called,
            "intent": str - Detected intent (greeting/casual/medical)
        }

    Best Practices:
        - Intent classification prevents unnecessary tool calls
        - Protects PHI by avoiding data exposure on casual messages
        - Always specify thread_id in config for checkpointer persistence
        - Pass context for custom state management
    """
    # Extract user_id from context or use default
    user_id = user_context.get("user_id", "default_user") if user_context else "default_user"
    
    # Get last user message for intent classification
    last_message = messages[-1].content if messages else ""
    
    # Classify intent
    intent = classify_intent(last_message)
    logger.debug(f"Classified intent: {intent} for message: '{last_message[:50]}...'")
    
    # Early exit for greetings/casual - no tool calls, no PHI exposure
    if intent in ["greeting", "casual"]:
        # Optionally get user name for personalization (lightweight query)
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
        logger.info(f"Quick response for {intent}: {len(response)} chars (no tools called)")
        return {
            "response": response,
            "tools_used": [],
            "intent": intent
        }
    
    # Medical query - proceed with full agent pipeline
    logger.info(f"Processing medical query with agent (user_id: {user_id})")

    # Trim message history to last 10 messages to reduce token usage
    if len(messages) > 10:
        messages = messages[-10:]
        logger.debug(f"Trimmed message history to last 10 messages")

    # Extract token for authenticated HTTP calls and set it globally
    token = user_context.get("token", "") if user_context else ""
    
    # Auto-set the token for HTTP-based tools (medication, reminders, adherence)
    if token:
        from app.agent.tools.http_client import set_agent_token
        set_agent_token(token)
        logger.debug("JWT token set for HTTP-based tools")
    
    # Create context following Context schema
    context = Context(user_id=user_id, token=token)

    # Config with thread_id - critical for checkpointer to save/load state
    # Each thread_id represents a separate conversation thread
    config = {"configurable": {"thread_id": user_id}}

    # Invoke agent with messages, context, and config
    result = agent.invoke(
        {"messages": messages},  # Message state is automatically maintained
        context=context,         # Custom context following Context schema
        config=config           # Configuration with thread_id for persistence
    )

    # Extract tools used from the result
    tools_used = []
    for message in result.get("messages", []):
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)
    
    logger.info(f"Tools used: {tools_used if tools_used else 'None'}")

    # Return response with metadata
    return {
        "response": result["messages"][-1].content,
        "tools_used": tools_used,
        "intent": intent
    }


def ask_agent_streaming(messages: list, user_context: dict = None, stream_mode: str = "values"):
    """
    Send messages to the AI agent and stream the response in real-time.

    Args:
        messages: Conversation history as list of Message objects (HumanMessage, AIMessage)
                 or dicts with {"role": "user"/"assistant", "content": "..."}
        user_context: Dict containing current user info, must include "user_id"
        stream_mode: "values" (full state) or "updates" (only changes)

    Yields:
        dict: Stream chunks containing intermediate results, tool calls, and final response

    Streaming Benefits:
        - Shows progress in real-time (tool calls, reasoning steps)
        - Better user experience with immediate feedback
        - Handles long-running tasks gracefully
    """
    try:
        # Extract user_id from context or use default
        user_id = user_context.get("user_id", "default_user") if user_context else "default_user"
        token = user_context.get("token", "") if user_context else ""

        # Auto-set the token for HTTP-based tools (medication, reminders, adherence)
        if token:
            from app.agent.tools.http_client import set_agent_token
            set_agent_token(token)

        # Create context with token for authenticated HTTP calls
        context = {"user_id": user_id, "token": token}

        # Config with thread_id - critical for checkpointer to save/load state
        config = {"configurable": {"thread_id": user_id}}

        # Stream agent responses in real-time (system_prompt already in create_agent)
        for chunk in agent.stream(
            {"messages": messages, "context": context, "remaining_steps": 10},  # State with messages, context, and steps
            config=config,           # Configuration with thread_id for persistence
            stream_mode=stream_mode  # "values" for full state, "updates" for changes only
        ):
            yield chunk
        
    except Exception as e:
        logger.error(f"Error in ask_agent_streaming: {e}", exc_info=True)
        # Yield an error message as the final chunk
        yield {"messages": [AIMessage(content="I'm sorry, I'm experiencing technical difficulties. Please try again later.")], "error": str(e)}

