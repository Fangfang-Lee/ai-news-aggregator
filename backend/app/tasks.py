from celery import Task
from sqlalchemy.orm import Session
import logging

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.rss_service import RSSService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""

    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def fetch_all_sources(self):
    """Fetch content from all active RSS sources"""
    try:
        logger.info("Starting to fetch content from all RSS sources")

        rss_service = RSSService(self.db)

        # Get all active sources
        from app.models.rss_models import RSSSource
        active_sources = self.db.query(RSSSource).filter(
            RSSSource.is_active == True
        ).all()

        total_fetched = 0

        for source in active_sources:
            try:
                success = rss_service.fetch_source_content(source.id)
                if success:
                    total_fetched += 1
                    logger.info(f"Fetched content from {source.name}")
            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}")

        logger.info(f"Completed fetching. Sources processed: {total_fetched}/{len(active_sources)}")

        return {
            'status': 'success',
            'sources_fetched': total_fetched,
            'total_sources': len(active_sources)
        }

    except Exception as e:
        logger.error(f"Error in fetch_all_sources task: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def fetch_source(self, source_id: int):
    """Fetch content from a specific RSS source"""
    try:
        logger.info(f"Fetching content from source ID: {source_id}")

        rss_service = RSSService(self.db)
        success = rss_service.fetch_source_content(source_id)

        if success:
            logger.info(f"Successfully fetched content from source ID: {source_id}")
            return {'status': 'success', 'source_id': source_id}
        else:
            logger.warning(f"Failed to fetch content from source ID: {source_id}")
            return {'status': 'failed', 'source_id': source_id}

    except Exception as e:
        logger.error(f"Error in fetch_source task: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=DatabaseTask)
def cleanup_old_content(self, days: int = 30):
    """Clean up content older than specified days (except bookmarked items)"""
    try:
        logger.info(f"Cleaning up content older than {days} days")

        from app.models.rss_models import Content, ReadingHistory, content_category
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find IDs of old, non-bookmarked content
        old_ids = [
            row[0] for row in
            self.db.query(Content.id).filter(
                Content.created_at < cutoff_date,
                Content.is_bookmarked == False
            ).all()
        ]

        if not old_ids:
            logger.info("No old content to clean up")
            return {'status': 'success', 'deleted_count': 0}

        # Cascade: delete related records first
        self.db.query(ReadingHistory).filter(
            ReadingHistory.content_id.in_(old_ids)
        ).delete(synchronize_session=False)

        self.db.execute(
            content_category.delete().where(
                content_category.c.content_id.in_(old_ids)
            )
        )

        # Delete the content itself
        deleted = self.db.query(Content).filter(
            Content.id.in_(old_ids)
        ).delete(synchronize_session=False)

        self.db.commit()

        logger.info(f"Cleaned up {deleted} old content items (with related data)")

        return {'status': 'success', 'deleted_count': deleted}

    except Exception as e:
        logger.error(f"Error in cleanup_old_content task: {e}")
        self.db.rollback()
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, base=DatabaseTask)
def generate_missing_summaries(self, batch_size: int = 20):
    """Generate AI summaries for articles that don't have one yet"""
    try:
        from app.models.rss_models import Content
        from app.services.summary_service import SummaryService
        from app.core.config import settings

        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API key not configured, skipping summary generation")
            return {'status': 'skipped', 'reason': 'no_api_key'}

        summary_service = SummaryService()

        # Find articles without AI-generated summaries
        # We look for articles that have content but summary is NULL or very short
        articles = self.db.query(Content).filter(
            Content.content_text.isnot(None),
            Content.content_text != '',
        ).order_by(Content.published_date.desc()).limit(batch_size).all()

        generated = 0
        skipped = 0

        for article in articles:
            # Skip if already has a decent summary (> 50 chars likely means AI-generated)
            if article.summary and len(article.summary) > 80:
                skipped += 1
                continue

            text_to_summarize = article.content_text or article.summary or article.title
            if not text_to_summarize or len(text_to_summarize.strip()) < 50:
                skipped += 1
                continue

            try:
                max_length = summary_service.get_dynamic_length(text_to_summarize)
                ai_summary = summary_service.generate_summary(text_to_summarize, max_length)
                if ai_summary:
                    article.summary = ai_summary
                    self.db.commit()
                    generated += 1
                    logger.info(f"Generated summary for: {article.title[:50]}")
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Error generating summary for article {article.id}: {e}")
                skipped += 1

        logger.info(f"Summary generation complete: {generated} generated, {skipped} skipped")
        return {'status': 'success', 'generated': generated, 'skipped': skipped}

    except Exception as e:
        logger.error(f"Error in generate_missing_summaries task: {e}")
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, base=DatabaseTask)
def initialize_default_data(self):
    """Initialize default categories and RSS sources (delegates to main.py)"""
    try:
        logger.info("Initializing default data via Celery task")

        from app.services.category_service import CategoryService
        from app.models.rss_models import RSSSource
        from app.main import _initialize_default_sources

        category_service = CategoryService(self.db)
        category_service.initialize_default_categories()

        existing_sources = self.db.query(RSSSource).count()
        if existing_sources == 0:
            _initialize_default_sources(self.db, category_service)

        logger.info("Default data initialization completed")
        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error in initialize_default_data task: {e}")
        return {'status': 'error', 'message': str(e)}
