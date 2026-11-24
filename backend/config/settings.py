import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    mistral_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    @field_validator(
        "openai_api_key",
        "anthropic_api_key",
        "google_api_key",
        "deepseek_api_key",
        "mistral_api_key",
        "groq_api_key",
        "openrouter_api_key",
        mode="before"
    )
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v

    openai_model: str = "gpt-4o"
    claude_model: str = "claude-3-5-sonnet-20241022"
    gemini_model: str = "gemini-2.0-flash"
    deepseek_model: str = "deepseek-chat"
    mistral_model: str = "mistral-large-latest"

    llm_timeout: int = 30
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "trust_llm"
    faiss_index_path: str = "data/faiss_index"
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5

    weight_agreement: float = 0.3
    weight_rag_validation: float = 0.5
    weight_completeness: float = 0.2


settings = Settings()
