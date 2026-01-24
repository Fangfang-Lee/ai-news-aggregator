from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.schemas import (
    RSSSourceResponse,
    RSSSourceCreate,
    RSSSourceUpdate,
    MessageResponse
)
from app.models.rss_models import RSSSource
from app.services.category_service import CategoryService
from app.services.rss_service import RSSService

router = APIRouter()


@router.get("/", response_model=List[RSSSourceResponse])
async def get_sources(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return")
):
    """Get all RSS sources with optional filtering"""
    service = RSSService(db)
    sources = await service.get_sources(
        category_id=category_id,
        skip=skip,
        limit=limit
    )
    return sources


@router.get("/{source_id}", response_model=RSSSourceResponse)
async def get_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific RSS source"""
    service = RSSService(db)
    source = await service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return source


@router.post("/", response_model=RSSSourceResponse)
async def create_source(
    source: RSSSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new RSS source"""
    # Validate category exists
    if source.category_id:
        category_service = CategoryService(db)
        if not await category_service.get_category(source.category_id):
            raise HTTPException(
                status_code=400,
                detail="Category not found"
            )

    service = RSSService(db)
    return await service.create_source(source)


@router.put("/{source_id}", response_model=RSSSourceResponse)
async def update_source(
    source_id: int,
    source_update: RSSSourceUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing RSS source"""
    service = RSSService(db)

    # If updating category, validate it exists
    if source_update.category_id is not None:
        category_service = CategoryService(db)
        if not await category_service.get_category(source_update.category_id):
            raise HTTPException(
                status_code=400,
                detail="Category not found"
            )

    updated_source = await service.update_source(source_id, source_update)
    if not updated_source:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return updated_source


@router.delete("/{source_id}", response_model=MessageResponse)
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Delete an RSS source"""
    service = RSSService(db)
    success = await service.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return MessageResponse(message="RSS source deleted successfully")


@router.post("/{source_id}/fetch", response_model=MessageResponse)
async def fetch_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger fetching from an RSS source"""
    service = RSSService(db)
    success = await service.fetch_source_content(source_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to fetch content from RSS source")
    return MessageResponse(message="Content fetching initiated successfully")


@router.get("/{source_id}/stats")
async def get_source_stats(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Get statistics for an RSS source"""
    service = RSSService(db)
    stats = await service.get_source_stats(source_id)
    if not stats:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return stats