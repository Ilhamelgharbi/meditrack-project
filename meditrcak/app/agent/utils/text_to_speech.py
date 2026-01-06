"""
Simple Text-to-Speech Functions and Test Route
"""

import logging
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import sys
import os

# Try to import from config, fallback to environment variables
try:
    # Add parent directory to path for config import
    if __name__ == "__main__":
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.config.settings import settings
except ImportError:
    # Fallback to environment variables
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

logger = logging.getLogger(__name__)


def tts_gtts(text: str) -> Dict[str, Any]:
    """Convert text to speech using Google TTS (free)"""
    try:
        # Create temp audio directory
        temp_dir = Path(settings.UPLOADS_PATH) / "audio" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = temp_dir / f"gtts_{timestamp}.mp3"

        # Google TTS API
        base_url = "https://translate.google.com/translate_tts"
        max_length = 200
        audio_chunks = []

        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            params = {
                "ie": "UTF-8", "q": chunk, "tl": "en",
                "client": "tw-ob", "ttsspeed": "1.0"
            }
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            audio_chunks.append(response.content)

        # Save combined audio
        with open(output_path, 'wb') as f:
            for chunk in audio_chunks:
                f.write(chunk)

        return {
            "success": True,
            "audio_path": str(output_path),
            "provider": "Google TTS",
            "text_length": len(text)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def tts_elevenlabs(text: str) -> Dict[str, Any]:
    """Convert text to speech using ElevenLabs (premium)"""
    try:
        if not ELEVENLABS_API_KEY:
            return {"success": False, "error": "ElevenLabs API key not configured"}

        # Create temp audio directory
        temp_dir = Path(settings.UPLOADS_PATH) / "audio" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = temp_dir / f"elevenlabs_{timestamp}.mp3"

        # ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()

        # Save audio
        with open(output_path, 'wb') as f:
            f.write(response.content)

        return {
            "success": True,
            "audio_path": str(output_path),
            "provider": "ElevenLabs",
            "text_length": len(text)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def tts(text: str, provider: str = "gtts") -> Dict[str, Any]:
    """Unified TTS function with fallback"""
    if provider == "elevenlabs":
        result = tts_elevenlabs(text)
        if not result["success"]:
            result = tts_gtts(text)
            result["fallback"] = "Used Google TTS"
        return result
    else:
        return tts_gtts(text)


# FastAPI route for testing
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    provider: Optional[str] = "gtts"

@router.post("/test-tts")
async def test_tts(request: TTSRequest):
    """Test TTS conversion and save to uploads/audio/temp"""
    try:
        result = tts(request.text, request.provider)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "message": "TTS conversion successful",
            "audio_path": result["audio_path"],
            "provider": result["provider"],
            "text_length": result["text_length"],
            "saved_to": "app/agent/uploads/audio/temp"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Test functions
if __name__ == "__main__":
    print("Testing TTS Functions...")

    test_text = "Hello, this is a test of text to speech conversion."

    # Test Google TTS
    print("\n1. Testing Google TTS:")
    result = tts_gtts(test_text)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Audio saved: {result['audio_path']}")

    # Test ElevenLabs
    print("\n2. Testing ElevenLabs:")
    result = tts_elevenlabs(test_text)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Audio saved: {result['audio_path']}")

    # Test unified
    print("\n3. Testing Unified (with fallback):")
    result = tts(test_text, "elevenlabs")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Audio saved: {result['audio_path']}")
        print(f"Provider: {result['provider']}")