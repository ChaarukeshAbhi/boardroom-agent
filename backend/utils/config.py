from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = ""
    RECALL_API_KEY: str = ""
    RECALL_WEBHOOK_URL: str = ""
    # Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")

    # App Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # Whisper
    WHISPER_MODEL: str = "base"  # for real-time / short chunks (speed)
    # Full meeting transcript: use "small" or "medium" for better accuracy
    WHISPER_TRANSCRIPTION_MODEL: str = "small"
    # Decode options for full transcript (higher = better accuracy, slower)
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_BEST_OF: int = 5

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".mp3", ".mp4", ".wav", ".m4a", ".webm"}

    class Config:
        env_file = ".env"
        extra = "ignore"   

settings = Settings()