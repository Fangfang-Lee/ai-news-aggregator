from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.schemas import MessageResponse
from app.services.content_service import ContentService
from app.core.config import settings
from datetime import datetime, timedelta
from app.models.rss_models import Content
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_cron_secret(request: Request):
    """Verify Vercel Cron secret"""
    # Vercel Cron sends authorization header or x-vercel-cron header
    auth_header = request.headers.get("authorization")
    vercel_cron = request.headers.get("x-vercel-cron")
    
    # Check for Vercel Cron header (most reliable)
    if vercel_cron:
        return True
    
    # Check for authorization header with secret
    if auth_header:
        expected = f"Bearer {settings.SECRET_KEY}"
        if auth_header == expected:
            return True
    
    # In production, require authentication
    if os.getenv("VERCEL") and not (vercel_cron or auth_header):
        raise HTTPException(status_code=403, detail="Invalid cron authorization")
    
    # Allow in development
    return True


@router.post("/fetch-all", response_model=MessageResponse)
async def cron_fetch_all(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_secret)
):
    """Cron endpoint to fetch content from all active RSS sources"""
    try:
        service = ContentService(db)
        count = await service.fetch_all_active_sources()
        logger.info(f"Cron job: Fetched content from {count} active sources")
        return MessageResponse(
            message=f"Successfully fetched content from {count} active sources"
        )
    except Exception as e:
        logger.error(f"Cron job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=MessageResponse)
async def cron_cleanup(
    request: Request,
    db: Session = Depends(get_db),
    days: int = 7,
    _: bool = Depends(verify_cron_secret)
):
    """Cron endpoint to cleanup old content"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted = db.query(Content).filter(
            Content.created_at < cutoff_date,
            Content.is_bookmarked == False
        ).delete()
        
        db.commit()
        
        logger.info(f"Cron job: Cleaned up {deleted} old content items")
        return MessageResponse(
            message=f"Successfully cleaned up {deleted} old content items"
        )
    except Exception as e:
        logger.error(f"Cron cleanup error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
