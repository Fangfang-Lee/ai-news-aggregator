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

    def get_content(
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

    def get_content_by_id(self, content_id: int) -> Optional[Content]:
        """Get content by ID"""
        return self.db.query(Content).filter(Content.id == content_id).first()

    def create_or_update_content(self, entry_data: dict, source_id: int) -> bool:
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

        # Date cutoff — skip articles published before the configured minimum date
        published_date = entry_data.get('published_date')
        if published_date and settings.CONTENT_MIN_DATE:
            min_date = datetime.strptime(settings.CONTENT_MIN_DATE, "%Y-%m-%d")
            if published_date < min_date:
                logger.debug(f"Skipped old article (before {settings.CONTENT_MIN_DATE}): "
                             f"{entry_data.get('title', '')[:60]}")
                return False

        title = self.parser.clean_text(entry_data.get('title', ''))[:512]
        raw_summary = entry_data.get('summary')
        cleaned_summary = self.parser.clean_text(raw_summary)[:2000] if raw_summary else None
        content_text = self.parser.clean_text(entry_data.get('content_text'))

        # Relevance filtering
        # Step 1: Blacklist — always filter out pure financial/stock noise
        if self.parser.is_financial_noise(title):
            logger.debug(f"Filtered financial noise: {title[:60]}")
            return False

        # Step 2: Keyword relevance check
        matched_category = self.parser.categorize_article(
            title, content_text or cleaned_summary or ''
        )
        category_id = entry_data.get('category_id')

        if category_id:
            # Source has preset category — check if it's a broad source
            BROAD_CATEGORIES = {'Internet', 'Technology', 'Startup & Product'}
            source_cat = self.db.query(Category).filter(Category.id == category_id).first()
            if source_cat and source_cat.name in BROAD_CATEGORIES and not matched_category:
                # Broad source + no keyword match → skip
                logger.debug(f"Skipped irrelevant from broad source: {title[:60]}")
                return False
        elif not matched_category:
            # No preset category + no keyword match → skip
            logger.debug(f"Skipped irrelevant article: {title[:60]}")
            return False

        # Get text for summarization (prefer content_text, fall back to summary)
        text_to_summarize = content_text or cleaned_summary or title

        # Generate AI summary if service is available
        ai_summary = None
        if self.summary_service and text_to_summarize:
            max_length = self.summary_service.get_dynamic_length(text_to_summarize)
            ai_summary = self.summary_service.generate_summary(text_to_summarize, max_length)
            if ai_summary:
                logger.info(f"Generated AI summary for article: {title[:50]}")

        # Create new content
        db_content = Content(
            title=title,
            summary=ai_summary or cleaned_summary,
            content_html=entry_data.get('content_html'),
            content_text=content_text,
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

        # Assign category: use source's preset category, or auto-detected category
        if category_id:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if category:
                db_content.categories.append(category)
        elif matched_category:
            category = self.db.query(Category).filter(Category.name == matched_category).first()
            if category:
                db_content.categories.append(category)

        self.db.commit()
        return True

    def mark_as_read(self, content_id: int) -> bool:
        """Mark content as read"""
        content = self.get_content_by_id(content_id)
        if not content:
            return False

        content.is_read = True
        self.db.commit()

        # Add to reading history
        history = ReadingHistory(content_id=content_id, read_duration=0)
        self.db.add(history)
        self.db.commit()

        return True

    def mark_as_unread(self, content_id: int) -> bool:
        """Mark content as unread"""
        content = self.get_content_by_id(content_id)
        if not content:
            return False

        content.is_read = False
        self.db.commit()
        return True

    def toggle_bookmark(self, content_id: int) -> Optional[bool]:
        """
        Toggle bookmark status

        Returns:
            New bookmark status or None if content not found
        """
        content = self.get_content_by_id(content_id)
        if not content:
            return None

        content.is_bookmarked = not content.is_bookmarked
        self.db.commit()
        return content.is_bookmarked

    def get_reading_history(self, limit: int = 50) -> List[ReadingHistory]:
        """Get reading history"""
        return self.db.query(ReadingHistory).order_by(
            ReadingHistory.read_at.desc()
        ).limit(limit).all()
