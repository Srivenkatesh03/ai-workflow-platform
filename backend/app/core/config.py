from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Workflow Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./workflow_platform.db"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    n8n_base_url: str = "http://localhost:5678"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # AI Config
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    mock_model: str = "mock-gpt-4"

    # Queue / Redis Config
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"




@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

