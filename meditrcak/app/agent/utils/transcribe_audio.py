# if you dont use pipenv uncomment the following:

from app.config.settings import settings

#Setup Speech to text–STT–model for transcription
import os
from groq import Groq

GROQ_API_KEY=settings.GROQ_API_KEY


def transcribe_with_groq(audio_filepath):
    
    try:
        client=Groq(api_key=settings.GROQ_API_KEY)
        stt_model="whisper-large-v3"
        audio_file=open(audio_filepath, "rb")
        transcription=client.audio.transcriptions.create(
            model=stt_model,
            file=audio_file,
            language="en"
    )
        return transcription.text
    except Exception as e:
        print(e)
        return 