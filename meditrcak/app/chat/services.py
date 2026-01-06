# app/chat/services.py
"""
Chat History Service - CRUD operations for conversation persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.chat.models import ChatMessage, MessageRole
import json
import logging

logger = logging.getLogger(__name__)


def save_message(
    db: Session,
    user_id: int,
    role: str,
    content: str,
    input_type: Optional[str] = None,
    image_url: Optional[str] = None,
    audio_url: Optional[str] = None,
    tools_used: Optional[List[str]] = None,
    intent: Optional[str] = None,
) -> ChatMessage:
    """
    Save a chat message to the database.
    
    Args:
        db: Database session
        user_id: User ID
        role: 'user' or 'assistant'
        content: Message content
        input_type: Type of input (text, voice, image, multimodal)
        image_url: URL or base64 of image
        audio_url: URL of audio file
        tools_used: List of tools used by agent
        intent: Detected intent
    
    Returns:
        Created ChatMessage object
    """
    try:
        message_role = MessageRole.user if role == "user" else MessageRole.assistant
        
        message = ChatMessage(
            user_id=user_id,
            role=message_role,
            content=content,
            input_type=input_type,
            image_url=image_url,
            audio_url=audio_url,
            tools_used=json.dumps(tools_used) if tools_used else None,
            intent=intent,
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.debug(f"Saved message for user {user_id}: {content[:50]}...")
        return message
        
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        db.rollback()
        raise


def get_user_history(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[ChatMessage]:
    """
    Get chat history for a user.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Max number of messages to return
        offset: Number of messages to skip
    
    Returns:
        List of ChatMessage objects ordered by created_at ascending
    """
    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get history for user {user_id}: {e}")
        return []


def get_recent_messages(
    db: Session,
    user_id: int,
    count: int = 10,
) -> List[ChatMessage]:
    """
    Get the most recent N messages for a user.
    
    Args:
        db: Database session
        user_id: User ID
        count: Number of recent messages
    
    Returns:
        List of ChatMessage objects ordered by created_at ascending
    """
    try:
        # Get recent messages in descending order, then reverse
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(count)
            .all()
        )
        # Reverse to get chronological order
        return list(reversed(messages))
        
    except Exception as e:
        logger.error(f"Failed to get recent messages for user {user_id}: {e}")
        return []


def clear_user_history(db: Session, user_id: int) -> int:
    """
    Clear all chat history for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        Number of messages deleted
    """
    try:
        count = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .delete()
        )
        db.commit()
        logger.info(f"Cleared {count} messages for user {user_id}")
        return count
        
    except Exception as e:
        logger.error(f"Failed to clear history for user {user_id}: {e}")
        db.rollback()
        return 0


def get_message_count(db: Session, user_id: int) -> int:
    """Get total message count for a user."""
    try:
        return db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
    except Exception as e:
        logger.error(f"Failed to get message count: {e}")
        return 0
