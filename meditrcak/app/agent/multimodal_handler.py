# multimodal_handler.py
"""
Multimodal Handler Subagent

This module provides a standalone handler for multimodal processing:
- Audio transcription (speech-to-text)
- Image analysis (optional)
- Text-to-speech generation

Based on the process_inputs logic pattern.
"""

import os
import logging
import base64
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def encode_image(image_filepath: str) -> str:
    """
    Encode image to base64 for API transmission.
    
    Args:
        image_filepath: Path to image file
    
    Returns:
        Base64 encoded image string
    """
    with open(image_filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def transcribe_with_groq(GROQ_API_KEY: str, audio_filepath: str, stt_model: str = "whisper-large-v3") -> str:
    """
    Transcribe audio using Groq Whisper API.
    
    Args:
        GROQ_API_KEY: Groq API key
        audio_filepath: Path to audio file
        stt_model: Speech-to-text model name
    
    Returns:
        Transcribed text
    """
    from groq import Groq
    
    client = Groq(api_key=GROQ_API_KEY)
    
    logger.info(f"Transcribing audio: {audio_filepath}")
    
    with open(audio_filepath, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=stt_model,
            file=audio_file,
            response_format="text",
            language="en",
            temperature=0.0
        )
    
    result = transcription if isinstance(transcription, str) else transcription.text
    logger.info(f"Transcription: '{result[:100]}...'")
    
    return result


def analyze_image_with_query(query: str, encoded_image: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> str:
    """
    Analyze image with a query using Groq Vision API.
    
    Args:
        query: Query text to analyze image with
        encoded_image: Base64 encoded image
        model: Vision model to use
    
    Returns:
        Analysis response text
    """
    from groq import Groq
    from app.config.settings import settings
    
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    logger.info(f"Analyzing image with query: '{query[:100]}...'")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                }
            ]
        }],
        max_tokens=1024,
        temperature=0.2
    )
    
    result = response.choices[0].message.content
    logger.info(f"Analysis result: '{result[:100]}...'")
    
    return result


def text_to_speech_with_elevenlabs(input_text: str, output_filepath: str = "final.mp3") -> str:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        input_text: Text to convert to speech
        output_filepath: Path to save audio file
    
    Returns:
        Path to generated audio file
    """
    import requests
    
    try:
        from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
    except ImportError:
        ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
        ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    if not ELEVENLABS_API_KEY or len(ELEVENLABS_API_KEY.strip()) == 0:
        logger.warning("ElevenLabs API key not configured, falling back to gTTS")
        return text_to_speech_with_gtts(input_text, output_filepath)
    
    logger.info(f"Generating speech with ElevenLabs: '{input_text[:100]}...'")
    
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": input_text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Ensure output directory exists
        output_path = Path(output_filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Audio saved to: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.warning(f"ElevenLabs TTS failed: {e}, falling back to gTTS")
        return text_to_speech_with_gtts(input_text, output_filepath)


def text_to_speech_with_gtts(input_text: str, output_filepath: str = "final.mp3") -> str:
    """
    Convert text to speech using Google TTS (fallback).
    
    Args:
        input_text: Text to convert to speech
        output_filepath: Path to save audio file
    
    Returns:
        Path to generated audio file
    """
    import requests
    from urllib.parse import quote
    
    logger.info(f"Generating speech with gTTS: '{input_text[:100]}...'")
    
    url = "https://translate.google.com/translate_tts"
    params = {
        "ie": "UTF-8",
        "q": input_text,
        "tl": "en",
        "client": "tw-ob",
        "textlen": len(input_text)
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    
    # Ensure output directory exists
    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    logger.info(f"Audio saved to: {output_path}")
    
    return str(output_path)


def process_inputs(
    audio_filepath: str,
    image_filepath: Optional[str] = None,
    system_prompt: str = "You are a medical assistant. Analyze the following: "
) -> Tuple[str, str, str]:
    """
    Main multimodal processing pipeline (Subagent H).
    
    This function replicates the process_inputs logic:
    1. Transcribe audio (speech-to-text)
    2. Analyze image with transcription as query (if image provided)
    3. Generate TTS audio response
    
    Args:
        audio_filepath: Path to audio file to transcribe
        image_filepath: Optional path to image file to analyze
        system_prompt: System prompt prepended to transcription for analysis
    
    Returns:
        Tuple of (transcription, doctor_response, voice_file_path)
    
    Example:
        >>> transcription, response, audio_path = process_inputs(
        ...     audio_filepath="patient_audio.wav",
        ...     image_filepath="xray.jpg",
        ...     system_prompt="You are a radiologist. "
        ... )
    """
    # Get API key from settings
    from app.config.settings import settings
    GROQ_API_KEY = settings.GROQ_API_KEY
    
    # Step 1: Transcribe audio
    logger.info("=" * 60)
    logger.info("STEP 1: Speech-to-Text")
    logger.info("=" * 60)
    
    speech_to_text_output = transcribe_with_groq(
        GROQ_API_KEY=GROQ_API_KEY,
        audio_filepath=audio_filepath,
        stt_model="whisper-large-v3"
    )
    
    # Step 2: Analyze image (if provided)
    logger.info("=" * 60)
    logger.info("STEP 2: Image Analysis")
    logger.info("=" * 60)
    
    if image_filepath:
        encoded_image = encode_image(image_filepath)
        query = system_prompt + speech_to_text_output
        
        doctor_response = analyze_image_with_query(
            query=query,
            encoded_image=encoded_image,
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        )
    else:
        doctor_response = "No image provided for me to analyze"
        logger.info("No image provided, using default response")
    
    # Step 3: Generate TTS audio
    logger.info("=" * 60)
    logger.info("STEP 3: Text-to-Speech")
    logger.info("=" * 60)
    
    voice_of_doctor = text_to_speech_with_elevenlabs(
        input_text=doctor_response,
        output_filepath="final.mp3"
    )
    
    logger.info("=" * 60)
    logger.info("Multimodal Processing Complete")
    logger.info("=" * 60)
    
    return speech_to_text_output, doctor_response, voice_of_doctor


# Alias for convenience
h = process_inputs  # Subagent H


if __name__ == "__main__":
    """
    Test the multimodal handler.
    
    Usage:
        python multimodal_handler.py <audio_file> [image_file]
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python multimodal_handler.py <audio_file> [image_file]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    image_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Process inputs
    try:
        transcription, response, audio_path = h(
            audio_filepath=audio_file,
            image_filepath=image_file
        )
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"\n📝 Transcription:\n{transcription}\n")
        print(f"💬 Response:\n{response}\n")
        print(f"🔊 Audio saved to: {audio_path}\n")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
