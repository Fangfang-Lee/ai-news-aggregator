from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.schemas import (
    ContentResponse,
    ContentListResponse,
    MessageResponse,
    SearchFilters
)
from app.services.content_service import ContentService

router = APIRouter()


@router.get("/", response_model=ContentListResponse)
async def get_content(
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
    return await service.get_content(
        category_id=category_id,
        source_id=source_id,
        is_read=is_read,
        is_bookmarked=is_bookmarked,
        search=search,
        page=page,
        page_size=page_size
    )


@router.post("/fetch-all", response_model=MessageResponse)
async def fetch_all_sources(
    db: Session = Depends(get_db)
):
    """Trigger fetching from all active RSS sources"""
    service = ContentService(db)
    count = await service.fetch_all_active_sources()
    return MessageResponse(
        message=f"Initiated content fetching from {count} active sources"
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content_item(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific content item"""
    service = ContentService(db)
    content = await service.get_content_by_id(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.post("/{content_id}/mark-read", response_model=MessageResponse)
async def mark_as_read(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Mark content as read"""
    service = ContentService(db)
    success = await service.mark_as_read(content_id)
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(message="Content marked as read")


@router.post("/{content_id}/mark-unread", response_model=MessageResponse)
async def mark_as_unread(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Mark content as unread"""
    service = ContentService(db)
    success = await service.mark_as_unread(content_id)
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(message="Content marked as unread")


@router.post("/{content_id}/bookmark", response_model=MessageResponse)
async def toggle_bookmark(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Toggle bookmark status of content"""
    service = ContentService(db)
    result = await service.toggle_bookmark(content_id)
    if not result:
        raise HTTPException(status_code=404, detail="Content not found")
    return MessageResponse(
        message=f"Content {'bookmarked' if result else 'unbookmarked'} successfully"
    )


@router.get("/categories/{category_id}", response_model=ContentListResponse)
async def get_content_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_unread_only: bool = Query(False, description="Show only unread items")
):
    """Get content by category"""
    service = ContentService(db)
    return await service.get_content(
        category_id=category_id,
        is_read=False if is_unread_only else None,
        page=page,
        page_size=page_size
    )