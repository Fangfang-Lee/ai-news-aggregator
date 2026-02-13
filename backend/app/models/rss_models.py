from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Association table for many-to-many relationship between content and categories
content_category = Table(
    'content_category',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)


class RSSSource(Base):
    __tablename__ = "rss_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_fetched = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="rss_sources")
    articles = relationship("Content", back_populates="rss_source")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#007bff")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    rss_sources = relationship("RSSSource", back_populates="category")
    contents = relationship("Content", secondary=content_category, back_populates="categories")


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    link = Column(String(2048), nullable=False)
    image_url = Column(String(512), nullable=True)
    author = Column(String(255), nullable=True)
    published_date = Column(DateTime, nullable=True, index=True)
    guid = Column(String(512), nullable=False, unique=True)
    source_url = Column(String(2048), nullable=False)
    categories = relationship("Category", secondary=content_category, back_populates="contents")
    rss_source_id = Column(Integer, ForeignKey("rss_sources.id"), index=True)
    is_read = Column(Boolean, default=False, index=True)
    is_bookmarked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    rss_source = relationship("RSSSource", back_populates="articles")


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False, index=True)
    read_at = Column(DateTime, server_default=func.now())
    read_duration = Column(Integer, default=0)  # seconds

    # Relationships
    content = relationship("Content")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(20), default="light")
    articles_per_page = Column(Integer, default=20)
    auto_refresh = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=300)  # seconds
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())