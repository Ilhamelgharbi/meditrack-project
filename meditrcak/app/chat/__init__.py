# app/chat/__init__.py
"""Chat module for conversation history persistence."""

from app.chat.models import ChatMessage, MessageRole

__all__ = ["ChatMessage", "MessageRole"]
