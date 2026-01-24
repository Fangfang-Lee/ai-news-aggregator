from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from datetime import datetime
import logging

from app.models.rss_models import Content, Category, ReadingHistory
from app.api.schemas import ContentListResponse
from app.crawlers.content_parser import ContentParser
from app.services.summary_service import SummaryService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContentService:
    """Service for content management"""

    def __init__(self, db: Session):
        self.db = db
        self.parser = ContentParser()
        self.summary_service = SummaryService() if settings.DEEPSEEK_API_KEY else None

    async def get_content(
        self,
        category_id: Optional[int] = None,
        source_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        is_bookmarked: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ContentListResponse:
        """Get content with filtering and pagination"""
        query = self.db.query(Content)

        # Apply filters
        if category_id is not None:
            query = query.join(Content.categories).filter(Category.id == category_id)

        if source_id is not None:
            query = query.filter(Content.rss_source_id == source_id)

        if is_read is not None:
            query = query.filter(Content.is_read == is_read)

        if is_bookmarked is not None:
            query = query.filter(Content.is_bookmarked == is_bookmarked)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Content.title.ilike(search_pattern),
                    Content.summary.ilike(search_pattern),
                    Content.content_text.ilike(search_pattern)
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        items = query.order_by(
            desc(Content.published_date),
            desc(Content.created_at)
        ).offset(offset).limit(page_size).all()

        return ContentListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    async def get_content_by_id(self, content_id: int) -> Optional[Content]:
        """Get content by ID"""
        return self.db.query(Content).filter(Content.id == content_id).first()

    async def create_or_update_content(self, entry_data: dict, source_id: int) -> bool:
        """
        Create or update content based on GUID

        Returns:
            True if new content was created, False if updated or skipped
        """
        # Check if content with same GUID exists
        existing = self.db.query(Content).filter(
            Content.guid == entry_data['guid']
        ).first()

        if existing:
            # Update existing content if needed
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return False

        # Get text for summarization (prefer content_text, fall back to summary)
        text_to_summarize = (
            entry_data.get('content_text') or
            entry_data.get('summary') or
            entry_data.get('title', '')
        )

        # Generate AI summary if service is available
        ai_summary = None
        if self.summary_service and text_to_summarize:
            max_length = self.summary_service.get_dynamic_length(text_to_summarize)
            ai_summary = await self.summary_service.generate_summary(text_to_summarize, max_length)
            if ai_summary:
                logger.info(f"Generated AI summary for article: {entry_data.get('title', 'Unknown')[:50]}")

        # Create new content
        db_content = Content(
            title=self.parser.clean_text(entry_data.get('title', ''))[:512],
            summary=ai_summary or self.parser.clean_text(entry_data.get('summary'))[:2000] if entry_data.get('summary') else None,
            content_html=entry_data.get('content_html'),
            content_text=self.parser.clean_text(entry_data.get('content_text')),
            link=entry_data.get('link'),
            image_url=entry_data.get('image_url'),
            author=entry_data.get('author'),
            published_date=entry_data.get('published_date'),
            guid=entry_data.get('guid'),
            source_url=entry_data.get('source_url'),
            rss_source_id=source_id
        )

        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)

        # Add category if provided
        category_id = entry_data.get('category_id')
        if category_id:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if category:
                db_content.categories.append(category)
                self.db.commit()

        return True

    async def mark_as_read(self, content_id: int) -> bool:
        """Mark content as read"""
        content = await self.get_content_by_id(content_id)
        if not content:
            return False

        content.is_read = True
        self.db.commit()

        # Add to reading history
        history = ReadingHistory(content_id=content_id, read_duration=0)
        self.db.add(history)
        self.db.commit()

        return True

    async def mark_as_unread(self, content_id: int) -> bool:
        """Mark content as unread"""
        content = await self.get_content_by_id(content_id)
        if not content:
            return False

        content.is_read = False
        self.db.commit()
        return True

    async def toggle_bookmark(self, content_id: int) -> Optional[bool]:
        """
        Toggle bookmark status

        Returns:
            New bookmark status or None if content not found
        """
        content = await self.get_content_by_id(content_id)
        if not content:
            return None

        content.is_bookmarked = not content.is_bookmarked
        self.db.commit()
        return content.is_bookmarked

    async def fetch_all_active_sources(self) -> int:
        """Fetch content from all active RSS sources"""
        from app.services.rss_service import RSSService
        from app.models.rss_models import RSSSource

        active_sources = self.db.query(RSSSource.id).filter(RSSSource.is_active == True).all()
        rss_service = RSSService(self.db)

        count = 0
        for (source_id,) in active_sources:
            try:
                await rss_service.fetch_source_content(source_id)
                count += 1
            except Exception as e:
                logger.error(f"Error fetching from source {source_id}: {e}")

        return count

    async def get_reading_history(self, limit: int = 50) -> List[ReadingHistory]:
        """Get reading history"""
        return self.db.query(ReadingHistory).order_by(
            ReadingHistory.read_at.desc()
        ).limit(limit).all()