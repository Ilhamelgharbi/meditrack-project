# tools/audio_transcribe.py
"""
Cloud-Based Audio Transcription Tool - Deployment Ready

Supported Providers (Online APIs):
- Groq Whisper API: Fast, uses existing GROQ_API_KEY (recommended)
- OpenAI Whisper API: Premium quality, requires OpenAI key
- Deepgram: Real-time streaming, perfect for LiveKit/WebSocket

No Local Processing - 100% Cloud-Based:
- No model downloads required
- No ffmpeg dependency
- Lightweight and scalable
- Perfect for serverless/container deployment
"""

import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from langchain.tools import tool, ToolRuntime

# Add parent directory to path for config import when running standalone
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _transcribe_with_groq(audio_file_path: Path) -> Dict[str, Any]:
    """
    Transcribe audio using Groq's Cloud Whisper API.
    Fast inference, uses existing GROQ_API_KEY.
    
    Args:
        audio_file_path: Path to audio file
    
    Returns:
        Dict with transcription results
    """
    try:
        from groq import Groq
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        logger.info(f"Calling Groq Whisper API for: {audio_file_path.name}")
        
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",  # Groq's Whisper model
                file=audio_file,
                response_format="verbose_json",  # Get detailed response with language, etc.
                language="en",  # Force English transcription
                temperature=0.0  # Deterministic output
            )
        
        return {
            "success": True,
            "audio_path": str(audio_file_path),
            "text": transcription.text,
            "language": getattr(transcription, 'language', 'unknown'),
            "duration": getattr(transcription, 'duration', None),
            "provider": "Groq Whisper API",
            "model": "whisper-large-v3"
        }
        
    except ImportError:
        return {
            "error": "Groq SDK not installed",
            "message": "Install: pip install groq"
        }
    except Exception as e:
        logger.error(f"Groq transcription error: {e}")
        return {
            "error": str(e),
            "provider": "Groq"
        }


def _transcribe_with_openai(audio_file_path: Path, api_key: str) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API (cloud).
    Requires OpenAI API key.
    
    Args:
        audio_file_path: Path to audio file
        api_key: OpenAI API key
    
    Returns:
        Dict with transcription results
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        logger.info(f"Calling OpenAI Whisper API for: {audio_file_path.name}")
        
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        return {
            "success": True,
            "audio_path": str(audio_file_path),
            "text": transcription.text,
            "language": getattr(transcription, 'language', 'unknown'),
            "duration": getattr(transcription, 'duration', None),
            "provider": "OpenAI Whisper API",
            "model": "whisper-1"
        }
        
    except ImportError:
        return {
            "error": "OpenAI SDK not installed",
            "message": "Install: pip install openai"
        }
    except Exception as e:
        logger.error(f"OpenAI transcription error: {e}")
        return {
            "error": str(e),
            "provider": "OpenAI"
        }


@tool("transcribe_audio", description="Transcribe audio file to text using cloud APIs (Groq/OpenAI). Cloud-based, no local processing. Supports MP3, WAV, M4A, OGG.")
def transcribe_audio(runtime: ToolRuntime, audio_path: str, provider: str = "groq") -> Dict[str, Any]:
    """
    Transcribe audio file using cloud-based Whisper APIs.
    
    Perfect for deployment: No local models, no ffmpeg, pure cloud processing.
    
    Args:
        runtime: Tool runtime context
        audio_path: Path to the audio file
        provider: API provider - "groq" (default, uses GROQ_API_KEY) or "openai"
    
    Returns:
        Dict with transcription text and metadata
    """
    # Validate API key
    if provider == "groq" and not GROQ_API_KEY:
        return {
            "error": "Groq API key not configured",
            "message": "Set GROQ_API_KEY in .env file",
            "instructions": [
                "1. Sign up at https://console.groq.com",
                "2. Generate an API key",
                "3. Add to .env: GROQ_API_KEY=your_key_here"
            ]
        }
    
    try:
        # Validate audio path
        audio_file = Path(audio_path)
        if not audio_file.exists():
            return {
                "error": "Audio file not found",
                "path": audio_path
            }
        
        if audio_file.suffix.lower() not in settings.ALLOWED_AUDIO_EXTENSIONS:
            return {
                "error": "Invalid audio format",
                "allowed_formats": settings.ALLOWED_AUDIO_EXTENSIONS,
                "received": audio_file.suffix
            }
        
        # Transcribe using cloud API
        if provider == "groq":
            result = _transcribe_with_groq(audio_file)
        elif provider == "openai":
            # OpenAI requires separate key
            openai_key = runtime.context.get("openai_api_key") if hasattr(runtime, 'context') else None
            if not openai_key:
                return {
                    "error": "OpenAI API key not provided",
                    "message": "Pass openai_api_key in context or use provider='groq'"
                }
            result = _transcribe_with_openai(audio_file, openai_key)
        else:
            return {
                "error": f"Unknown provider: {provider}",
                "supported_providers": ["groq", "openai"]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        return {
            "error": str(e),
            "audio_path": audio_path
        }


# @tool("transcribe_audio_streaming", description="Get real-time streaming transcription info. Use for LiveKit/WebSocket integration. Returns setup instructions.")
# def transcribe_audio_streaming(runtime: ToolRuntime) -> Dict[str, Any]:
#     """
#     Provides information for real-time streaming transcription.
#     For LiveKit or WebSocket integration.
    
#     Args:
#         runtime: Tool runtime context
    
#     Returns:
#         Dict with streaming setup information
#     """
#     return {
#         "streaming_providers": {
#             "deepgram": {
#                 "best_for": "Real-time streaming with WebSockets",
#                 "sdk": "pip install deepgram-sdk",
#                 "api_url": "wss://api.deepgram.com/v1/listen",
#                 "features": ["Real-time", "Word timestamps", "Low latency"],
#                 "livekit_compatible": True,
#                 "code_example": "https://github.com/deepgram/deepgram-python-sdk"
#             },
#             "groq": {
#                 "best_for": "File-based transcription (fast inference)",
#                 "sdk": "pip install groq",
#                 "features": ["Fast", "Accurate", "Uses existing GROQ_API_KEY"],
#                 "livekit_compatible": False,
#                 "note": "Use for file uploads, not real-time streams"
#             },
#             "assemblyai": {
#                 "best_for": "Real-time streaming with advanced features",
#                 "sdk": "pip install assemblyai",
#                 "features": ["Real-time", "Speaker diarization", "Sentiment analysis"],
#                 "livekit_compatible": True
#             }
#         },
#         "recommended_for_deployment": {
#             "file_upload": "Use transcribe_audio tool with Groq",
#             "livekit": "Use Deepgram WebSocket in LiveKit agent",
#             "react_websocket": "Use Deepgram or AssemblyAI streaming",
#             "whatsapp": "Use transcribe_audio tool with Groq (file-based)"
#         },
#         "livekit_integration": {
#             "docs": "https://docs.livekit.io/agents/",
#             "example": "LiveKit Agents SDK has built-in Deepgram support",
#             "quick_start": "https://docs.livekit.io/agents/start/voice-ai/"
#         }
#     }


# Example usage
if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    print("Audio Transcription Tools")
    print("=" * 60)
    
    runtime = MagicMock()
    
    # Test cloud transcription
    print("\n1. Cloud Transcription (Groq):")
    result = transcribe_audio.func(runtime, "uploads/audio/2/audio_20251214_154832_928137d4.wav", provider="groq")
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
        if "instructions" in result:
            print("\n   Setup Instructions:")
            for instruction in result["instructions"]:
                print(f"     {instruction}")
    else:
        print(f"   ✅ Success!")
        print(f"   Provider: {result.get('provider', 'Unknown')}")
        print(f"   Model: {result.get('model', 'Unknown')}")
        print(f"   Language: {result.get('language', 'Unknown')}")
        print(f"   Text preview: {result['text'][:100] if len(result['text']) > 100 else result['text']}...")
    
    # # Test streaming info
    # print("\n2. Streaming Transcription Info:")
    # result2 = transcribe_audio_streaming.func(runtime)
    # if "streaming_providers" in result2:
    #     print(f"   Available providers: {', '.join(result2['streaming_providers'].keys())}")
    #     print(f"\n   Recommended for:")
    #     for use_case, solution in result2["recommended_for_deployment"].items():
    #         print(f"     • {use_case}: {solution}")
    #     print(f"\n   LiveKit integration: {result2['livekit_integration']['docs']}")
