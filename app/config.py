"""
Application configuration using Pydantic Settings.
Supports dynamic switching between VLM providers (Qwen, OpenAI, or Mock).
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Service Information
    APP_NAME: str = "Multimodal Document Intelligence Pipeline"
    VERSION: str = "1.0.0"
    ENV: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = False
    
    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 2
    
    # VLM Extraction Engine
    # 'mock' for local CI/CD & testing, 'openai' for GPT-4o, 'qwen' for local GPU serving
    VLM_PROVIDER: Literal["mock", "openai", "qwen"] = "mock"
    
    # Model Configurations
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-2024-08-06"
    
    QWEN_MODEL_ID: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    QWEN_DEVICE: str = "cuda"  # "cuda" or "cpu"
    QWEN_TORCH_DTYPE: str = "bfloat16"
    QWEN_LOAD_IN_4BIT: bool = True
    
    # Preprocessing & Resolution Tuning
    DPI_SCALING: int = 200
    MAX_IMAGE_DIMENSION: int = 2048
    MIN_IMAGE_DIMENSION: int = 512
    CONTRAST_ENHANCE_FACTOR: float = 1.2
    
    # Post-Processing & Validation Thresholds
    CONFIDENCE_THRESHOLD: float = 0.85
    MATH_TOLERANCE_DELTA: float = 0.05
    AUTO_FLAG_ON_DISCREPANCY: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
