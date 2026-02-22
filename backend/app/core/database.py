from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

db_url = settings.DATABASE_URL

# Force psycopg2 driver (sync) instead of asyncpg
# Replace postgresql:// with postgresql+psycopg2:// if not already specified
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Supabase-hosted Postgres typically requires SSL. Prefer putting `sslmode=require`
# directly in DATABASE_URL, but also support DATABASE_SSLMODE for convenience.
connect_args = {}
try:
    parsed = make_url(db_url)
    has_sslmode = "sslmode" in (parsed.query or {})
except Exception:
    has_sslmode = "sslmode=" in db_url

if not has_sslmode and settings.DATABASE_SSLMODE:
    # psycopg2 supports sslmode in connect_args
    connect_args["sslmode"] = settings.DATABASE_SSLMODE

engine_kwargs = {"pool_pre_ping": True}
if connect_args:
    engine_kwargs["connect_args"] = connect_args

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
