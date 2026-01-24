from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "ai_news_aggregator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Configure beat scheduler
celery_app.conf.beat_schedule = {
    'fetch-rss-feeds-every-5-minutes': {
        'task': 'app.tasks.fetch_all_sources',
        'schedule': 300.0,  # 5 minutes
    },
    'cleanup-old-content-daily': {
        'task': 'app.tasks.cleanup_old_content',
        'schedule': 86400.0,  # 24 hours
    },
}