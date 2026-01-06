# whatsapp/media_tools.py
"""
Media handling utilities for WhatsApp integration.
Processes images and audio sent via WhatsApp.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from app.agent.tools.image_analysis import identify_pill, analyze_medical_image
from app.agent.tools.audio_transcribe import transcribe_audio

logger = logging.getLogger(__name__)


def process_whatsapp_image(image_path: str, context: str = "general") -> Dict[str, Any]:
    """
    Process an image received via WhatsApp.
    
    Args:
        image_path: Path to the saved image file
        context: Context hint (e.g., "pill", "skin", "wound")
    
    Returns:
        Dict with processing results
    """
    try:
        from unittest.mock import MagicMock
        
        runtime = MagicMock()
        
        # Route to appropriate image analysis
        if context.lower() == "pill":
            result = identify_pill.func(runtime, image_path)
            
            if "error" in result:
                return {
                    "success": False,
                    "message": "Could not analyze pill image",
                    "error": result["error"]
                }
            
            return {
                "success": True,
                "type": "pill_identification",
                "result": result["most_likely"],
                "confidence": result["confidence"],
                "message": f"Identified as: {result['most_likely']} (confidence: {result['confidence']:.1%})"
            }
        
        else:
            # General medical image analysis
            result = analyze_medical_image.func(runtime, image_path, context)
            
            if "error" in result:
                return {
                    "success": False,
                    "message": "Could not analyze image",
                    "error": result["error"]
                }
            
            return {
                "success": True,
                "type": "medical_image_analysis",
                "result": result["top_assessment"],
                "message": f"Analysis: {result['top_assessment']}"
            }
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return {
            "success": False,
            "message": "Image processing failed",
            "error": str(e)
        }


def process_whatsapp_audio(audio_path: str) -> Dict[str, Any]:
    """
    Process audio received via WhatsApp.
    
    Args:
        audio_path: Path to the saved audio file
    
    Returns:
        Dict with transcription results
    """
    try:
        from unittest.mock import MagicMock
        
        runtime = MagicMock()
        
        # Transcribe audio
        result = transcribe_audio.func(runtime, audio_path)
        
        if "error" in result:
            return {
                "success": False,
                "message": "Could not transcribe audio",
                "error": result["error"]
            }
        
        return {
            "success": True,
            "type": "audio_transcription",
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "message": f"Transcription: {result['text']}"
        }
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return {
            "success": False,
            "message": "Audio processing failed",
            "error": str(e)
        }


def determine_media_context(message_text: str) -> str:
    """
    Determine context from user's message text.
    
    Args:
        message_text: Text accompanying the media
    
    Returns:
        Context string (pill, skin, wound, general)
    """
    text = message_text.lower()
    
    # Keywords for different contexts
    pill_keywords = ["pill", "medication", "medicine", "tablet", "capsule", "drug"]
    skin_keywords = ["skin", "rash", "redness", "spot", "acne", "itch"]
    wound_keywords = ["wound", "cut", "injury", "bruise", "burn", "scar"]
    
    if any(keyword in text for keyword in pill_keywords):
        return "pill"
    elif any(keyword in text for keyword in skin_keywords):
        return "skin condition"
    elif any(keyword in text for keyword in wound_keywords):
        return "wound"
    else:
        return "general"


def save_whatsapp_media(media_url: str, user_id: str, media_type: str) -> Optional[str]:
    """
    Download and save media from WhatsApp.
    
    Args:
        media_url: URL of the media file
        user_id: User identifier
        media_type: Type of media (image/audio)
    
    Returns:
        Path to saved file or None if failed
    """
    try:
        import requests
        from datetime import datetime
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
        
        # Download with Twilio authentication
        response = requests.get(
            media_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10
        )
        response.raise_for_status()
        
        # Determine save directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if media_type == "image":
            directory = Path("uploads/images")
            extension = ".jpg"
        elif media_type == "audio":
            directory = Path("uploads/audio")
            extension = ".ogg"
        else:
            return None
        
        directory.mkdir(parents=True, exist_ok=True)
        
        # Save file
        filename = f"whatsapp_{user_id}_{timestamp}{extension}"
        filepath = directory / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Saved WhatsApp media: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Failed to save WhatsApp media: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("WhatsApp Media Tools")
    print("=" * 60)
    
    # Test context determination
    print("\n1. Context Determination:")
    test_messages = [
        "What is this pill?",
        "I have a rash on my arm",
        "Look at this wound",
        "Can you analyze this?"
    ]
    
    for msg in test_messages:
        context = determine_media_context(msg)
        print(f"   '{msg}' -> {context}")
    
    # Test image processing (placeholder)
    print("\n2. Image Processing:")
    print("   Note: Requires actual image file and ML models")
    print("   Example: process_whatsapp_image('uploads/images/pill.jpg', 'pill')")
    
    # Test audio processing (placeholder)
    print("\n3. Audio Processing:")
    print("   Note: Requires actual audio file and Whisper model")
    print("   Example: process_whatsapp_audio('uploads/audio/voice.ogg')")
