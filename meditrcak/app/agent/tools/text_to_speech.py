# tools/text_to_speech.py
"""
Online Text-to-Speech Tools - API-Based (No Local Processing)

Providers:
- gTTS API: Free Google Text-to-Speech via online API
- ElevenLabs API: Premium AI voice synthesis via cloud API

Optimizations:
- Pure API calls - no local audio processing
- Validates API keys before calls to avoid wasting credits
- Lightweight and cloud-deployment ready
- Fast response times with direct API integration
"""

import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from langchain.tools import tool, ToolRuntime

# Add parent directory to path for config import when running standalone
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Cache validation state to avoid repeated failed API calls
_elevenlabs_available = None


def _check_elevenlabs_available() -> bool:
    """
    Check if ElevenLabs is available (has valid API key).
    Caches result to avoid repeated checks.
    
    Returns:
        True if ElevenLabs is available, False otherwise
    """
    global _elevenlabs_available
    
    if _elevenlabs_available is not None:
        return _elevenlabs_available
    
    if not settings.ELEVENLABS_API_KEY or len(settings.ELEVENLABS_API_KEY.strip()) == 0:
        logger.info("ElevenLabs API key not configured")
        _elevenlabs_available = False
        return False
    
    _elevenlabs_available = True
    return True


def _text_to_speech_gtts(text: str, output_path: Path) -> Dict[str, Any]:
    """
    Convert text to speech using Google Translate TTS API (online).
    No API key required - direct API call.
    
    Args:
        text: Text to convert
        output_path: Path to save audio file
    
    Returns:
        Dict with results
    """
    try:
        import requests
        from urllib.parse import quote
        
        logger.info(f"Calling Google TTS API for {len(text)} characters")
        
        # Google Translate TTS endpoint (public, no auth required)
        base_url = "https://translate.google.com/translate_tts"
        
        # Split long text into chunks (Google has 200 char limit per request)
        max_length = 200
        audio_chunks = []
        
        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            
            params = {
                "ie": "UTF-8",
                "q": chunk,
                "tl": "en",
                "client": "tw-ob",
                "ttsspeed": "1.0"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            audio_chunks.append(response.content)
        
        # Combine audio chunks
        with open(output_path, 'wb') as f:
            for chunk in audio_chunks:
                f.write(chunk)
        
        return {
            "success": True,
            "audio_path": str(output_path),
            "text_length": len(text),
            "provider": "Google TTS API (Free)",
            "format": "mp3",
            "api_endpoint": "translate.google.com"
        }
        
    except Exception as e:
        logger.error(f"Google TTS API error: {e}")
        return {
            "error": str(e),
            "provider": "Google TTS API",
            "fallback": "Try gTTS library: pip install gtts"
        }


def _text_to_speech_elevenlabs(text: str, output_path: Path) -> Dict[str, Any]:
    """
    Convert text to speech using ElevenLabs Cloud API (premium).
    Direct API call to cloud service - no local processing.
    
    Args:
        text: Text to convert
        output_path: Path to save audio file
    
    Returns:
        Dict with results
    """
    try:
        import requests
        
        # ElevenLabs Cloud API endpoint
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVENLABS_API_KEY
        }
        
        # Optimized settings for online/cloud usage
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2",  # Fast cloud model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        logger.info(f"Calling ElevenLabs Cloud API for {len(text)} characters")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save audio from cloud API response
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return {
            "success": True,
            "audio_path": str(output_path),
            "text_length": len(text),
            "provider": "ElevenLabs Cloud API",
            "voice_id": ELEVENLABS_VOICE_ID,
            "model": "eleven_turbo_v2",
            "format": "mp3",
            "api_endpoint": "api.elevenlabs.io"
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # Mark as unavailable to prevent future attempts
            global _elevenlabs_available
            _elevenlabs_available = False
            logger.error("ElevenLabs API key invalid - disabling for this session")
        return {
            "error": f"ElevenLabs API error: {e.response.status_code}",
            "fallback_available": True
        }
    except Exception as e:
        logger.error(f"ElevenLabs error: {e}")
        return {
            "error": str(e),
            "fallback_available": True
        }


@tool("tts_gtts", description="Convert text to speech using Google's online TTS API. Free, no API key required. Cloud-based processing.")
def tts_gtts(runtime: ToolRuntime, text: str, output_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert text to speech using Google Translate TTS API (online cloud service).
    
    Args:
        runtime: Tool runtime context
        text: Text to convert to speech
        output_filename: Optional filename for output audio (default: auto-generated)
    
    Returns:
        Dict with audio file path and metadata
    """
    # Generate output filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tts_gtts_test.mp3"
    
    # Ensure audio uploads directory exists
    audio_dir = Path(UPLOADS_PATH) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / output_filename
    
    return _text_to_speech_gtts(text, output_path)


@tool("tts_elevenlabs", description="Convert text to premium natural speech using ElevenLabs Cloud API. Online AI processing. Requires API key.")
def tts_elevenlabs(runtime: ToolRuntime, text: str, output_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert text to speech using ElevenLabs Cloud API (premium online service).
    
    Args:
        runtime: Tool runtime context
        text: Text to convert to speech
        output_filename: Optional filename for output audio (default: auto-generated)
    
    Returns:
        Dict with audio file path and metadata
    """
    if not _check_elevenlabs_available():
        return {
            "error": "ElevenLabs API key not configured or invalid",
            "message": "Set ELEVENLABS_API_KEY in .env file",
            "instructions": [
                "1. Sign up at https://elevenlabs.io",
                "2. Go to Settings > API Keys",
                "3. Create a new API key",
                "4. Add to .env: ELEVENLABS_API_KEY=your_key_here"
            ]
        }
    
    # Generate output filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tts_elevenlabs-test.mp3"
    
    # Ensure audio uploads directory exists
    audio_dir = Path(UPLOADS_PATH) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / output_filename
    
    return _text_to_speech_elevenlabs(text, output_path)


# @tool("text_to_speech_stream", description="Stream text-to-speech audio in real-time. Use for live voice responses.")
# def text_to_speech_stream(runtime: ToolRuntime, text: str) -> Dict[str, Any]:
#     """
#     Stream text-to-speech audio in real-time (ElevenLabs only).
    
#     Args:
#         runtime: Tool runtime context
#         text: Text to convert to speech
    
#     Returns:
#         Dict with streaming information
#     """
#     if not _check_elevenlabs_available():
#         return {
#             "error": "ElevenLabs API key not configured or invalid",
#             "message": "Streaming requires ElevenLabs. Use text_to_speech for gTTS fallback."
#         }
    
#     try:
#         import requests
        
#         url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
        
#         headers = {
#             "Accept": "audio/mpeg",
#             "Content-Type": "application/json",
#             "xi-api-key": ELEVENLABS_API_KEY
#         }
        
#         data = {
#             "text": text,
#             "model_id": "eleven_monolingual_v1",
#             "voice_settings": {
#                 "stability": 0.5,
#                 "similarity_boost": 0.5
#             }
#         }
        
#         logger.info(f"Streaming TTS for {len(text)} characters")
#         response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
#         response.raise_for_status()
        
#         # For streaming, we'd typically yield chunks
#         # This simplified version returns metadata
#         return {
#             "success": True,
#             "streaming": True,
#             "text_length": len(text),
#             "message": "Use streaming endpoint in FastAPI router for actual streaming"
#         }
        
#     except Exception as e:
#         logger.error(f"TTS streaming error: {e}")
#         return {
#             "error": str(e),
#             "text_preview": text[:50] + "..."
#         }


# Example usage
if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    print("Text-to-Speech Tools")
    print("=" * 60)
    
    runtime = MagicMock()
    
    test_text = "hi, tell me what i my medicaton , and how to treat the ancer"
    
    # Test ElevenLabs only
    # print("\n1. ElevenLabs TTS (Premium):")
    # result = tts_elevenlabs.func(runtime, test_text)
    
    # if "error" in result:
    #     print(f"   ❌ Error: {result['error']}")
    #     if "instructions" in result:
    #         print("\n   Setup Instructions:")
    #         for instruction in result["instructions"]:
    #             print(f"     {instruction}")
    # else:
    #     print(f"   ✅ Success: {result['success']}")
    #     print(f"   Provider: {result.get('provider', 'Unknown')}")
    #     print(f"   Audio Path: {result['audio_path']}")
    #     print(f"   Format: {result['format']}")
    
    # Test gTTS
    print("\n2. gTTS (Free):")
    output_path = Path(settings.UPLOADS_PATH) / "audio" / "test_gtts.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result2 = _text_to_speech_gtts(test_text, output_path)
    if "error" in result2:
        print(f"   ❌ Error: {result2['error']}")
    else:
        print(f"   ✅ Success: {result2['success']}")
        print(f"   Provider: {result2.get('provider', 'Unknown')}")
        print(f"   Audio Path: {result2['audio_path']}")
        print(f"   Format: {result2['format']}")
    
    # # Test streaming
    # print("\n2. Text-to-Speech Streaming:")
    # result2 = text_to_speech_stream.func(runtime, test_text)
    # if "error" in result2:
    #     print(f"   Error: {result2['error']}")
    # else:
    #     print(f"   Streaming: {result2.get('streaming', False)}")
