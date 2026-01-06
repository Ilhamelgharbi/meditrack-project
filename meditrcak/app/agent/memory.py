# memory.py
"""
LangChain Memory Management following official best practices.

Two Types of Memory:
1. Short-term memory (checkpointer): Conversation history within a thread
2. Long-term memory (store): Persistent user data across sessions

Based on: https://docs.langchain.com/oss/python/langchain/short-term-memory
          https://docs.langchain.com/oss/python/langchain/long-term-memory

Usage:
    # Short-term (conversation history)
    from memory import get_checkpointer
    checkpointer = get_checkpointer(use_persistent=True)
    
    # Long-term (user preferences, facts)
    from memory import get_memory_store, save_user_memory, get_user_memory
    store = get_memory_store()
"""

import logging
from typing import Optional
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from app.config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================================
# LONG-TERM MEMORY (Store)
# ============================================================================
# Stores persistent user data: preferences, facts, history across sessions
# Organized by namespace (user_id, context) and key

_memory_store = None


def get_memory_store() -> InMemoryStore:
    """
    Get or create the long-term memory store (cached).
    
    This store persists user data across sessions:
    - User preferences (language, communication style)
    - User facts (name, medical conditions, allergies)
    - Application context (last conversation topic, etc.)
    
    Returns:
        InMemoryStore instance (in production, use DB-backed store)
    """
    global _memory_store
    
    if _memory_store is not None:
        return _memory_store
    
    # TODO: In production, use PostgresStore or other DB-backed store
    # Example: from langgraph.store.postgres import PostgresStore
    #          _memory_store = PostgresStore(conn_string=POSTGRES_MEMORY_URI)
    
    logger.info("Initializing InMemoryStore for long-term memory")
    _memory_store = InMemoryStore()
    
    return _memory_store


def save_user_memory(user_id: str, key: str, data: dict, context: str = "general"):
    """
    Save user-specific long-term memory.
    
    Args:
        user_id: User identifier
        key: Memory key (e.g., "preferences", "medical_profile", "facts")
        data: Dictionary of data to store
        context: Application context (e.g., "general", "medical", "chat")
    
    Example:
        save_user_memory("user_123", "preferences", {
            "language": "English",
            "communication_style": "concise"
        })
    """
    store = get_memory_store()
    namespace = (user_id, context)
    store.put(namespace, key, data)
    logger.debug(f"Saved memory for user {user_id} [{context}:{key}]")


def get_user_memory(user_id: str, key: str, context: str = "general") -> Optional[dict]:
    """
    Retrieve user-specific long-term memory.
    
    Args:
        user_id: User identifier
        key: Memory key to retrieve
        context: Application context
    
    Returns:
        Dictionary of stored data or None if not found
    """
    store = get_memory_store()
    namespace = (user_id, context)
    item = store.get(namespace, key)
    
    if item:
        logger.debug(f"Retrieved memory for user {user_id} [{context}:{key}]")
        return item.value
    
    logger.debug(f"No memory found for user {user_id} [{context}:{key}]")
    return None


def search_user_memories(user_id: str, query: str, context: str = "general", limit: int = 5):
    """
    Search user memories by content similarity.
    
    Args:
        user_id: User identifier
        query: Search query
        context: Application context
        limit: Maximum number of results
    
    Returns:
        List of matching memory items
    """
    store = get_memory_store()
    namespace = (user_id, context)
    
    try:
        results = store.search(namespace, query=query, limit=limit)
        logger.debug(f"Found {len(results)} memories for query: {query}")
        return [item.value for item in results]
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        return []


# ============================================================================
# SHORT-TERM MEMORY (Checkpointer)
# ============================================================================
# Stores conversation history within a thread/session
# Enables conversation continuity and context retention


def get_checkpointer(use_persistent: bool = False):
    """
    Get checkpointer for short-term memory (conversation history).
    
    Checkpointers persist conversation state across invocations:
    - Messages history (user inputs and agent responses)
    - Agent state (custom fields like user_id, preferences)
    - Tool call results and intermediate steps
    
    Best Practices (from LangChain docs):
    - Use InMemorySaver for development/testing
    - Use PostgresSaver for production with multiple instances
    - Use SqliteSaver for single-instance deployments
    - Always pass thread_id in config to maintain conversation context
    
    Args:
        use_persistent: If True, attempts persistent storage (Postgres/SQLite)
                       If False, uses InMemorySaver (default)
    
    Returns:
        Checkpointer instance for use with create_agent()
    
    Example:
        checkpointer = get_checkpointer(use_persistent=True)
        agent = create_agent(model, tools, checkpointer=checkpointer)
        
        # Invoke with thread_id to persist conversation
        agent.invoke(
            {"messages": [{"role": "user", "content": "Hello"}]},
            config={"configurable": {"thread_id": "user_123"}}
        )
    """
    if not use_persistent:
        logger.info("Using InMemorySaver for short-term memory (non-persistent)")
        return InMemorySaver()
    
    # Try PostgreSQL first (production recommended)
    if settings.POSTGRES_MEMORY_URI:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver  # type: ignore
            
            checkpointer = PostgresSaver.from_conn_string(settings.POSTGRES_MEMORY_URI)
            checkpointer.setup()  # Auto-create tables
            logger.info("Using PostgresSaver for persistent short-term memory")
            return checkpointer
            
        except ImportError:
            logger.warning("PostgresSaver not available. Install: pip install langgraph-checkpoint-postgres")
        except Exception as e:
            logger.error(f"Failed to initialize PostgresSaver: {e}")
    
    # Fallback to SQLite (local persistent)
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"):
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore
            
            # Extract sqlite path from DATABASE_URL
            sqlite_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")
            
            # SqliteSaver automatically creates tables
            checkpointer = SqliteSaver.from_conn_string(sqlite_path)
            logger.info(f"Using SqliteSaver for persistent short-term memory: {sqlite_path}")
            return checkpointer
            
        except ImportError:
            logger.warning("SqliteSaver not available. Install: pip install langgraph-checkpoint-sqlite")
        except Exception as e:
            logger.error(f"Failed to initialize SqliteSaver: {e}")
    
    # Final fallback to InMemory
    logger.warning("No persistent storage configured. Falling back to InMemorySaver.")
    logger.info("To enable persistence:")
    logger.info("  1. Set POSTGRES_MEMORY_URI in .env for production")
    logger.info("  2. Or use sqlite DATABASE_URL for local testing")
    return InMemorySaver()


def get_conversation_history(checkpointer, thread_id: str, limit: int = 20):
    """
    Retrieve conversation history for a specific thread.
    
    Note: The agent automatically manages conversation history through
    the checkpointer. You typically don't need to call this directly.
    
    Args:
        checkpointer: The checkpointer instance
        thread_id: Unique identifier for the conversation thread (user_id)
        limit: Maximum number of messages to retrieve
    
    Returns:
        List of messages from the conversation history
    
    Example:
        checkpointer = get_checkpointer(use_persistent=True)
        messages = get_conversation_history(checkpointer, "user_123", limit=10)
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = checkpointer.get(config)
        
        if state and "messages" in state:
            messages = state["messages"]
            return messages[-limit:] if len(messages) > limit else messages
        
        logger.debug(f"No conversation history found for thread: {thread_id}")
        return []
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversation history: {e}")
        return []


def clear_conversation_history(checkpointer, thread_id: str):
    """
    Clear conversation history for a specific thread.
    
    Warning: This permanently deletes all conversation history for the thread.
    Use with caution in production.
    
    Args:
        checkpointer: The checkpointer instance
        thread_id: Unique identifier for the conversation thread
    
    Returns:
        bool: True if successful, False otherwise
    
    Example:
        checkpointer = get_checkpointer(use_persistent=True)
        success = clear_conversation_history(checkpointer, "user_123")
    """
    try:
        from langchain.messages import RemoveMessage  # type: ignore
        from langgraph.graph.message import REMOVE_ALL_MESSAGES  # type: ignore
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use RemoveMessage to properly clear history
        checkpointer.put(config, {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
        })
        
        logger.info(f"Cleared conversation history for thread: {thread_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {e}")
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_thread_state(checkpointer, thread_id: str) -> Optional[dict]:
    """
    Get the full state for a thread (including custom state fields).
    
    Args:
        checkpointer: The checkpointer instance
        thread_id: Thread identifier
    
    Returns:
        Full state dictionary or None if not found
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = checkpointer.get(config)
        
        if state:
            logger.debug(f"Retrieved state for thread: {thread_id}")
            return state
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve thread state: {e}")
        return None


def list_all_threads(checkpointer) -> list:
    """
    List all conversation threads in the checkpointer.
    
    Note: Only works with database-backed checkpointers (Postgres/SQLite).
    
    Args:
        checkpointer: The checkpointer instance
    
    Returns:
        List of thread_ids
    """
    try:
        # This method varies by checkpointer type
        # Implementation depends on underlying storage
        logger.warning("list_all_threads() implementation depends on checkpointer type")
        return []
        
    except Exception as e:
        logger.error(f"Failed to list threads: {e}")
        return []


# ============================================================================
# BEST PRACTICES & EXAMPLES
# ============================================================================

# Example: Using checkpointer with agent (from LangChain docs)
"""
from langchain.agents import create_agent
from memory import get_checkpointer

# Create checkpointer
checkpointer = get_checkpointer(use_persistent=True)

# Create agent with checkpointer
agent = create_agent(
    model="gpt-4o",
    tools=[tool1, tool2],
    checkpointer=checkpointer
)

# Invoke with thread_id for conversation continuity
config = {"configurable": {"thread_id": "user_123"}}

# First conversation
agent.invoke(
    {"messages": [{"role": "user", "content": "Hi, I'm Bob"}]},
    config=config
)

# Later conversation (remembers Bob's name)
agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config=config
)
# Response: "Your name is Bob!"
"""

# Example: Using long-term memory in tools (from LangChain docs)
"""
from langchain.tools import tool, ToolRuntime
from memory import get_memory_store

@tool
def get_user_preferences(runtime: ToolRuntime) -> str:
    '''Get user's preferences.'''
    store = runtime.store  # Store passed from agent
    user_id = runtime.context.user_id
    
    prefs = store.get(("users",), user_id)
    return str(prefs.value) if prefs else "No preferences set"

# Create agent with store
agent = create_agent(
    model="gpt-4o",
    tools=[get_user_preferences],
    store=get_memory_store(),  # Pass store to agent
    context_schema=Context
)
"""
