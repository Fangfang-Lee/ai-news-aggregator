from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.redis_client import redis_client


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    return redis_client
