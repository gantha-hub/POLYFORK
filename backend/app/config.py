"""Configuration settings for VrikshaVision Backend.

Loads environment variables from .env file using Pydantic Settings.
"""

from pathlib import Path
from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    # Project Information
    PROJECT_NAME: str = "VrikshaVision: Tree Digital Twin"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./data/vrikshavision.db"

    # Security
    API_KEY: str = ""

    # ML Backend Options
    MODEL_BACKEND: Literal["mock", "torch"] = "mock"
    WEIGHTS_PATH: str = "./weights/tree_detector_weights.pt"

    # File and Storage
    MAX_UPLOAD_SIZE_MB: int = 250
    ALLOWED_EXTENSIONS: List[str] = ["tif", "tiff", "jpg", "jpeg", "png"]
    UPLOAD_DIR: Path = Path("./data/uploads")
    RESULTS_DIR: Path = Path("./data/results")
    EXPORTS_DIR: Path = Path("./data/exports")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure runtime directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
