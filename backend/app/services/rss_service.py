from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging

from app.models.rss_models import RSSSource, Content
from app.api.schemas import RSSSourceCreate, RSSSourceUpdate
from app.crawlers.rss_crawler import RSSCrawler
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)


class RSSService:
    """Service for RSS source management"""

    def __init__(self, db: Session):
        self.db = db
        self.crawler = RSSCrawler()

    async def get_sources(
        self,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RSSSource]:
        """Get RSS sources with optional filtering"""
        query = self.db.query(RSSSource)

        if category_id is not None:
            query = query.filter(RSSSource.category_id == category_id)

        return query.order_by(RSSSource.name).offset(skip).limit(limit).all()

    async def get_source(self, source_id: int) -> Optional[RSSSource]:
        """Get RSS source by ID"""
        return self.db.query(RSSSource).filter(RSSSource.id == source_id).first()

    async def create_source(self, source: RSSSourceCreate) -> RSSSource:
        """Create a new RSS source"""
        # Validate RSS URL
        if not self.crawler.validate_feed_url(source.url):
            raise ValueError(f"Invalid RSS feed URL: {source.url}")

        db_source = RSSSource(**source.model_dump())
        self.db.add(db_source)
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    async def update_source(self, source_id: int, source_update: RSSSourceUpdate) -> Optional[RSSSource]:
        """Update an existing RSS source"""
        db_source = await self.get_source(source_id)
        if not db_source:
            return None

        update_data = source_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_source, field, value)

        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    async def delete_source(self, source_id: int) -> bool:
        """Delete an RSS source"""
        db_source = await self.get_source(source_id)
        if not db_source:
            return False

        self.db.delete(db_source)
        self.db.commit()
        return True

    async def fetch_source_content(self, source_id: int) -> bool:
        """Fetch content from a specific RSS source"""
        source = await self.get_source(source_id)
        if not source or not source.is_active:
            return False

        try:
            entries = self.crawler.fetch_and_parse(
                source.url,
                source.category_id
            )

            if not entries:
                logger.warning(f"No entries fetched from source {source.name}")
                return False

            content_service = ContentService(self.db)
            new_count = 0

            for entry in entries:
                created = await content_service.create_or_update_content(
                    entry,
                    source_id=source.id
                )
                if created:
                    new_count += 1

            # Update last_fetched timestamp
            source.last_fetched = datetime.utcnow()
            self.db.commit()

            logger.info(f"Fetched {len(entries)} entries from {source.name}, {new_count} new")
            return True

        except Exception as e:
            logger.error(f"Error fetching content from source {source.name}: {e}")
            return False

    async def get_source_stats(self, source_id: int) -> Optional[Dict]:
        """Get statistics for an RSS source"""
        source = await self.get_source(source_id)
        if not source:
            return None

        total_articles = self.db.query(Content).filter(
            Content.rss_source_id == source_id
        ).count()

        unread_articles = self.db.query(Content).filter(
            Content.rss_source_id == source_id,
            Content.is_read == False
        ).count()

        return {
            "source_id": source_id,
            "name": source.name,
            "total_articles": total_articles,
            "unread_articles": unread_articles,
            "last_fetched": source.last_fetched.isoformat() if source.last_fetched else None
        }