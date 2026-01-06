import os
import json
from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = os.environ.get("APP_NAME", "MediTrack")
    DEBUG: bool = os.environ.get("DEBUG", "true").lower() == "true"

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "dummy-key")
    ELEVENLABS_API_KEY: str = os.environ.get("ELEVENLABS_API_KEY", "dummy-key")
    
    # FDA API
    FDA_API_KEY: str = os.environ.get("FDA_API_KEY", "")
    OPENFDA_API_BASE: str = os.environ.get("OPENFDA_API_BASE", "https://api.fda.gov")
    
    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    
    # LiveKit Configuration (Real-time audio/video)
    LIVEKIT_API_KEY: str = os.environ.get("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.environ.get("LIVEKIT_API_SECRET", "")
    LIVEKIT_URL: str = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    
    # AI/RAG Settings
    DB_FAISS_PATH: str = os.environ.get("DB_FAISS_PATH", "app/agent/vectorstore/db_faiss")
    PDF_DATA_PATH: str = os.environ.get("PDF_DATA_PATH", "app/agent/data/")
    GROQ_MODEL_NAME: str = os.environ.get("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
    EMBEDDING_MODEL_NAME: str = os.environ.get("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Audio/Image Processing
    WHISPER_MODEL_SIZE: str = os.environ.get("WHISPER_MODEL_SIZE", "base")
    IMAGE_RECOGNITION_MODEL: str = os.environ.get("IMAGE_RECOGNITION_MODEL", "openai/clip-vit-base-patch32")
    ELEVENLABS_VOICE_ID: str = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    # ML Models (Predictive Analytics)
    HEART_DISEASE_MODEL_PATH: str = os.environ.get("HEART_DISEASE_MODEL_PATH", "data/models/heart_disease_model.pkl")
    DIABETES_MODEL_PATH: str = os.environ.get("DIABETES_MODEL_PATH", "data/models/diabetes_model.pkl")
    
    # Optional settings
    UPLOADS_PATH: str = os.environ.get("UPLOADS_PATH", "app/agent/uploads/")
    VECTORSTORE_PATH: str = os.environ.get("VECTORSTORE_PATH", "app/agent/vectorstore/")
    MAX_CHUNK_SIZE: int = int(os.environ.get("MAX_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.environ.get("CHUNK_OVERLAP", "50"))
    MAX_FILE_SIZE_MB: int = int(os.environ.get("MAX_FILE_SIZE_MB", "10"))
    API_TIMEOUT_SECONDS: int = int(os.environ.get("API_TIMEOUT_SECONDS", "30"))
    MAX_CONVERSATION_HISTORY: int = int(os.environ.get("MAX_CONVERSATION_HISTORY", "20"))
    ENABLE_WEB_SCRAPING: bool = os.environ.get("ENABLE_WEB_SCRAPING", "false").lower() == "true"
    ENABLE_WHATSAPP: bool = os.environ.get("ENABLE_WHATSAPP", "false").lower() == "true"
    ENABLE_LIVEKIT: bool = os.environ.get("ENABLE_LIVEKIT", "false").lower() == "true"
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '../../testagent.db'))}")
    POSTGRES_MEMORY_URI: str = os.environ.get("POSTGRES_MEMORY_URI", "")
    
    # AI Frontend Settings
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000/chatbot/ask")
    TOOL_URL: str = os.environ.get("TOOL_URL", "http://localhost:8000/chatbot/tool")
    V1_SERVER_PORT: int = int(os.environ.get("V1_SERVER_PORT", "8000"))
    
    # AI Prompts
    SYSTEM_PROMPT: str = os.environ.get("SYSTEM_PROMPT", "You are a helpful AI assistant.")
    
    # File Extensions
    ALLOWED_IMAGE_EXTENSIONS: ClassVar[list] = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_AUDIO_EXTENSIONS: ClassVar[list] = [".mp3", ".wav", ".m4a", ".ogg"]
    ALLOWED_PDF_EXTENSIONS: ClassVar[list] = [".pdf"]
    
    @property
    def cors_origins_list(self) -> list:
        cors_str = os.environ.get("CORS_ORIGINS_LIST", '["*"]')
        try:
            return json.loads(cors_str)
        except json.JSONDecodeError:
            # Fallback to comma-separated string
            return [origin.strip() for origin in cors_str.split(",")]
    class Config:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


settings = Settings()
