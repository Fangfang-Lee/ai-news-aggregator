from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_news_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8001", "http://127.0.0.1:8001"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # RSS Crawler
    RSS_FETCH_INTERVAL: int = 300  # seconds
    CONTENT_MIN_DATE: str = "2026-02-10"  # 只保留此日期及之后的文章

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
