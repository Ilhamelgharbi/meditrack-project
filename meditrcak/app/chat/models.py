# app/chat/models.py
"""
Chat History Models for persisting conversation history in SQLite.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(Base):
    """Stores individual chat messages for conversation history."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Optional metadata
    input_type = Column(String(20), nullable=True)  # text, voice, image, multimodal
    image_url = Column(Text, nullable=True)  # Base64 or path to image
    audio_url = Column(String(255), nullable=True)
    tools_used = Column(Text, nullable=True)  # JSON string of tools used
    intent = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    user = relationship("User", backref="chat_messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, user_id={self.user_id}, role={self.role})>"

    def to_dict(self):
        """Convert message to dictionary for API responses."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "input_type": self.input_type,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "tools_used": self.tools_used,
            "intent": self.intent,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
