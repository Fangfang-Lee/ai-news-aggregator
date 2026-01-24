from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_news_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # RSS Crawler
    RSS_FETCH_INTERVAL: int = 300  # 5 minutes
    MAX_WORKERS: int = 5

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""  # DeepSeek API Key for summarization
    SUMMARY_MAX_LENGTH: int = 300  # Maximum summary length

    class Config:
        env_file = ".env"


settings = Settings()