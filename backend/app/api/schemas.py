from pydantic import BaseModel, HttpUrl, Field
from pydantic.functional_serializers import PlainSerializer
from typing import Optional, List, Annotated
from datetime import datetime, timezone


def _serialize_utc_datetime(v: datetime) -> Optional[str]:
    """Serialize naive datetime as UTC (append Z suffix)"""
    if v is None:
        return None
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc).isoformat()
    return v.isoformat()


# Custom datetime type that always serializes with UTC timezone
UTCDatetime = Annotated[datetime, PlainSerializer(_serialize_utc_datetime, return_type=str)]


# RSS Source Schemas
class RSSSourceBase(BaseModel):
    name: str = Field(..., description="RSS source name")
    url: str = Field(..., description="RSS feed URL")
    description: Optional[str] = Field(None, description="RSS source description")
    category_id: Optional[int] = Field(None, description="Category ID")


class RSSSourceCreate(RSSSourceBase):
    pass


class RSSSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class RSSSourceResponse(RSSSourceBase):
    id: int
    is_active: bool
    last_fetched: Optional[UTCDatetime] = None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    class Config:
        from_attributes = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color: str = Field("#007bff", description="Category color (hex)")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: UTCDatetime

    class Config:
        from_attributes = True


# Content Schemas
class ContentBase(BaseModel):
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    content_html: Optional[str] = Field(None, description="HTML content")
    content_text: Optional[str] = Field(None, description="Plain text content")
    link: str = Field(..., description="Article link")
    image_url: Optional[str] = Field(None, description="Article image URL")
    author: Optional[str] = Field(None, description="Article author")
    published_date: Optional[UTCDatetime] = Field(None, description="Publication date")


class ContentResponse(ContentBase):
    id: int
    guid: str
    source_url: str
    rss_source_id: Optional[int]
    categories: List[CategoryResponse] = []
    is_read: bool
    is_bookmarked: bool
    created_at: UTCDatetime

    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int


# Reading History Schema
class ReadingHistoryResponse(BaseModel):
    id: int
    content_id: int
    read_at: UTCDatetime
    read_duration: int

    class Config:
        from_attributes = True


# API Response Schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Search Schema
class SearchFilters(BaseModel):
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    is_read: Optional[bool] = None
    is_bookmarked: Optional[bool] = None
    date_from: Optional[UTCDatetime] = None
    date_to: Optional[UTCDatetime] = None
