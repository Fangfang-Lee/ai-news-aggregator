from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.schemas import (
    ContentResponse,
    ContentListResponse,
    MessageResponse,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.get("/", response_model=ContentListResponse)
def get_content(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    source_id: Optional[int] = Query(None, description="Filter by source"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_bookmarked: Optional[bool] = Query(None, description="Filter by bookmarked status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get all content with filtering and pagination"""
    service = ContentService(db)
    return service.get_content(
        category_id=category_id,
        source_id=source_id,
        is_read=is_read,
        is_bookmarked=is_bookmarked,
        search=search,
        page=page,
        page_size=page_size
    )


@router.post("/fetch-all", response_model=MessageResponse)
def fetch_all_sources(
    db: Session = Depends(get_db)
):
    """Trigger fetching from all active RSS sources"""
    from app.services.rss_service import RSSService
    rss_service = RSSService(db)
    count = rss_service.fetch_all_active_sources()
    return MessageResponse(
        message=f"Initiated content fetching from {count} active sources"
    )


@router.post("/generate-summaries", response_model=MessageResponse)
def generate_summaries(
    batch_size: int = Query(20, ge=1, le=100, description="Number of articles to process"),
):
    """Trigger AI summary generation for articles missing summaries"""
    from app.tasks import generate_missing_summaries
    task = generate_missing_summaries.delay(batch_size)
    return MessageResponse(
        message=f"Summary generation task queued (task_id={task.id}, batch_size={batch_size})"
    )


@router.get("/{content_id}", response_model=ContentResponse)
def get_content_item(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific content item"""
    service = ContentService(db)
    content = service.get_content_by_id(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.post("/{content_id}/mark-read", response_model=MessageResponse)
def mark_as_read(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Mark content as read"""
    service = ContentService(db)
    success = service.mark_as_read(content_id)
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(message="Content marked as read")


@router.post("/{content_id}/mark-unread", response_model=MessageResponse)
def mark_as_unread(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Mark content as unread"""
    service = ContentService(db)
    success = service.mark_as_unread(content_id)
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(message="Content marked as unread")


@router.post("/{content_id}/bookmark", response_model=MessageResponse)
def toggle_bookmark(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Toggle bookmark status of content"""
    service = ContentService(db)
    result = service.toggle_bookmark(content_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(
        message=f"Content {'bookmarked' if result else 'unbookmarked'} successfully"
    )


@router.get("/categories/{category_id}", response_model=ContentListResponse)
def get_content_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_unread_only: bool = Query(False, description="Show only unread items")
):
    """Get content by category"""
    service = ContentService(db)
    return service.get_content(
        category_id=category_id,
        is_read=False if is_unread_only else None,
        page=page,
        page_size=page_size
    )
