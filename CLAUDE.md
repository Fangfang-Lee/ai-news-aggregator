# AI News Aggregator Project Guide

## Commands

- **Start Services**: `docker-compose up -d` (Runs on port 8080)
- **Rebuild Services**: `docker-compose up -d --build`
- **Stop Services**: `docker-compose down`
- **Reset Data**: `docker-compose down -v` (Clears database volume)
- **View Logs**: `docker-compose logs -f backend` (or `celery_worker`)
- **Run Tests**: `docker-compose exec backend pytest tests/`
- **Shell Access**: `docker-compose exec backend /bin/bash`
- **Database Shell**: `docker-compose exec postgres psql -U postgres -d ai_news_db`

## Architecture

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (SQLAlchemy ORM + psycopg2)
- **Queue/Cache**: Redis + Celery
- **Frontend**: Vanilla JavaScript + Jinja2 Templates
- **Deployment**: Docker Compose (Local), Render (Production)

## Code Style

- **Python**: Follow PEP 8. Use type hints (`typing` module).
- **Imports**: Group imports: standard lib, third-party, local app modules.
- **Async**: Use `async/await` for API routes; synchronous `psycopg2` for database.
- **Language**: Source code comments in English; Content/Data in Chinese (CN).
- **Error Handling**: Log errors with `logging` module; return appropriate HTTP status codes.

## Project Structure

- `backend/app`: Main application code
  - `api/`: REST API routes and Pydantic schemas
  - `core/`: Configuration and database setup
  - `crawlers/`: RSS parsing logic (using `feedparser` + `jieba`)
  - `models/`: SQLAlchemy database models
  - `services/`: Business logic (Category, Content, RSS)
  - `tasks.py`: Celery tasks for background fetching
- `frontend/`: Static assets (CSS, JS) and HTML templates
- `docker-compose.yml`: Service orchestration configuration

## Tech Stack Details

- **NLP**: Uses `jieba` for Chinese segmentation and keyword extraction.
- **RSS**: `feedparser` for fetching; Custom `ContentParser` for cleaning/deduplication.
- **Driver**: Explicitly uses `psycopg2-binary` for PostgreSQL to avoid asyncpg compatibility issues.
