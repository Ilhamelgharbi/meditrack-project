# whatsapp/handler.py
"""
Twilio WhatsApp Message Handler.
Receives WhatsApp messages, processes with agent, sends responses.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, Form, HTTPException
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from langchain_core.messages import HumanMessage
from app.agent.agent import ask_agent
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# Initialize Twilio client
_twilio_client = None


def get_twilio_client():
    """Get or create Twilio client (cached)."""
    global _twilio_client
    
    if _twilio_client is not None:
        return _twilio_client
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured")
        return None
    
    try:
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized")
        return _twilio_client
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
        return None


@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    ProfileName: str = Form(None)
):
    """
    WhatsApp webhook endpoint for incoming messages.
    
    Args:
        From: Sender's WhatsApp number (format: whatsapp:+1234567890)
        Body: Message text content
        NumMedia: Number of media attachments
        MediaUrl0: URL of first media attachment
        ProfileName: Sender's WhatsApp profile name
    
    Returns:
        TwiML response
    """
    if not settings.ENABLE_WHATSAPP:
        raise HTTPException(status_code=403, detail="WhatsApp integration is disabled")
    
    try:
        logger.info(f"WhatsApp message from {From} ({ProfileName}): {Body[:50]}...")
        
        # Extract user ID from phone number
        # Format: whatsapp:+1234567890 -> 1234567890
        user_id = From.replace("whatsapp:", "").replace("+", "")
        
        # Build context
        user_context = {
            "user_id": user_id,
            "phone_number": From,
            "profile_name": ProfileName or "Unknown",
            "channel": "whatsapp"
        }
        
        # Handle media (if present)
        media_response = ""
        if NumMedia > 0 and MediaUrl0:
            media_response = handle_media(MediaUrl0, user_id)
        
        # Get agent response
        messages = [HumanMessage(content=Body)]
        result = ask_agent(messages, user_context)
        
        response_text = result["response"] if isinstance(result, dict) else result
        
        # Combine media response if present
        if media_response:
            response_text = f"{media_response}\n\n{response_text}"
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        logger.info(f"Sent WhatsApp response to {From}")
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        
        # Send error message to user
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error processing your message. Please try again.")
        
        return str(resp)


def handle_media(media_url: str, user_id: str) -> str:
    """
    Handle media attachments (images/audio) from WhatsApp.
    
    Args:
        media_url: URL of the media file
        user_id: User identifier
    
    Returns:
        Response message about media processing
    """
    try:
        import requests
        from pathlib import Path
        from datetime import datetime
        
        logger.info(f"Downloading media: {media_url}")
        
        # Download media
        client = get_twilio_client()
        if not client:
            return "Media processing unavailable (Twilio not configured)"
        
        # Get media with authentication
        response = requests.get(
            media_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10
        )
        response.raise_for_status()
        
        # Determine media type from content-type
        content_type = response.headers.get('content-type', '')
        
        if 'image' in content_type:
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"whatsapp_{user_id}_{timestamp}.jpg"
            filepath = Path("uploads/images") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved image: {filepath}")
            return f"📷 Image received and saved. Analyzing..."
            
        elif 'audio' in content_type:
            # Save audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"whatsapp_{user_id}_{timestamp}.ogg"
            filepath = Path("uploads/audio") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved audio: {filepath}")
            return f"🎤 Voice message received. Transcribing..."
            
        else:
            return f"📎 Media received (type: {content_type})"
        
    except Exception as e:
        logger.error(f"Media handling error: {e}")
        return f"⚠️ Could not process media: {str(e)}"


def send_whatsapp_message(to: str, message: str) -> bool:
    """
    Send a WhatsApp message proactively.
    
    Args:
        to: Recipient's WhatsApp number (format: whatsapp:+1234567890)
        message: Message text to send
    
    Returns:
        bool: True if sent successfully
    """
    client = get_twilio_client()
    
    if not client:
        logger.error("Cannot send WhatsApp message: Twilio not configured")
        return False
    
    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to
        )
        
        logger.info(f"Sent WhatsApp message to {to}: {msg.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return False


# Example usage
if __name__ == "__main__":
    print("WhatsApp Handler Module")
    print("=" * 60)
    
    if not ENABLE_WHATSAPP:
        print("\n⚠️  WhatsApp integration is disabled")
        print("   Set ENABLE_WHATSAPP=true in .env to enable")
    else:
        print(f"\n✓ WhatsApp enabled")
        print(f"  From Number: {TWILIO_WHATSAPP_NUMBER}")
        
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            print("\n⚠️  Twilio credentials not configured")
            print("   Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env")
