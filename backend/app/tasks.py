from celery import Task
from sqlalchemy.orm import Session
import logging
import asyncio

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.rss_service import RSSService
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)

def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


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
        content_service = ContentService(self.db)

        # Get all active sources
        from app.models.rss_models import RSSSource
        active_sources = self.db.query(RSSSource).filter(
            RSSSource.is_active == True
        ).all()

        total_fetched = 0
        total_new = 0

        for source in active_sources:
            try:
                success = _run_async(rss_service.fetch_source_content(source.id))
                if success:
                    total_fetched += 1
                    logger.info(f"Fetched content from {source.name}")
            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}")

        logger.info(f"Completed fetching. Sources: {total_fetched}, Total new articles: {total_new}")

        return {
            'status': 'success',
            'sources_fetched': total_fetched,
            'new_articles': total_new
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
        success = _run_async(rss_service.fetch_source_content(source_id))

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

        from app.models.rss_models import Content
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old content that is not bookmarked and not read
        deleted = self.db.query(Content).filter(
            Content.created_at < cutoff_date,
            Content.is_bookmarked == False
        ).delete()

        self.db.commit()

        logger.info(f"Cleaned up {deleted} old content items")

        return {'status': 'success', 'deleted_count': deleted}

    except Exception as e:
        logger.error(f"Error in cleanup_old_content task: {e}")
        self.db.rollback()
        return {'status': 'error', 'message': str(e)}


@celery_app.task(bind=True, base=DatabaseTask)
def initialize_default_data(self):
    """Initialize default categories and sample RSS sources"""
    try:
        logger.info("Initializing default data")

        from app.services.category_service import CategoryService
        from app.api.schemas import RSSSourceCreate

        # Initialize default categories
        category_service = CategoryService(self.db)
        _run_async(category_service.initialize_default_categories())
        logger.info("Initialized default categories")

        # Add sample RSS sources
        rss_service = RSSService(self.db)

        # Sample AI/Tech RSS sources (Chinese Context)
        sample_sources = [
            {
                'name': '机器之心',
                'url': 'https://www.jiqizhixin.com/rss',
                'description': '国内领先的人工智能专业媒体',
                'category_id': None  # Will be assigned to AI category
            },
            {
                'name': '36氪 - AI',
                'url': 'https://36kr.com/feed/tags/ai',
                'description': '36氪人工智能板块',
                'category_id': None
            },
            {
                'name': 'InfoQ - AI',
                'url': 'https://www.infoq.cn/feed/topic/106',
                'description': 'InfoQ 中国 AI 频道',
                'category_id': None
            },
            {
                'name': '少数派',
                'url': 'https://sspai.com/feed',
                'description': '高效工作生活与数字产品',
                'category_id': None
            }
        ]

        # Get AI category
        ai_category = _run_async(category_service.get_category_by_name('人工智能'))

        for source_data in sample_sources:
            try:
                # Assign categories based on source name
                if '机器之心' in source_data['name'] or '36氪' in source_data['name'] or 'InfoQ' in source_data['name']:
                    source_data['category_id'] = ai_category.id if ai_category else None
                else:
                    tech_cat = _run_async(category_service.get_category_by_name('科技前沿'))
                    source_data['category_id'] = tech_cat.id if tech_cat else None

                _run_async(rss_service.create_source(RSSSourceCreate(**source_data)))
                logger.info(f"Added RSS source: {source_data['name']}")
            except ValueError as e:
                logger.warning(f"Could not add {source_data['name']}: {e}")
            except Exception as e:
                logger.error(f"Error adding {source_data['name']}: {e}")

        logger.info("Default data initialization completed")

        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error in initialize_default_data task: {e}")
        return {'status': 'error', 'message': str(e)}