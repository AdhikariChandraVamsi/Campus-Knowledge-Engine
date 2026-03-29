"""
Central configuration — reads from .env.
Import `settings` anywhere in the app. Never import os.environ directly.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App
    APP_NAME: str = "Campus Knowledge Engine"
    APP_ENV: str = "development"
    SECRET_KEY: str = "default_secret_key_for_local_testing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///test.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_store"
    CHROMA_COLLECTION_NAME: str = "academic_chunks"

    # Gemini
    GEMINI_API_KEY: str = ""

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Retrieval
    SIMILARITY_THRESHOLD: float = 0.45

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50


settings = Settings()

# Ensure dirs exist at startup
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
