import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_category(db):
    """Create a sample category for testing"""
    from app.models.rss_models import Category
    category = Category(
        name="AI",
        description="Artificial Intelligence",
        color="#6366f1"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def sample_source(db, sample_category):
    """Create a sample RSS source for testing"""
    from app.models.rss_models import RSSSource
    source = RSSSource(
        name="Test Feed",
        url="https://example.com/feed",
        description="Test RSS feed",
        category_id=sample_category.id
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@pytest.fixture
def sample_content(db, sample_source):
    """Create sample content for testing"""
    from app.models.rss_models import Content
    content = Content(
        title="Test Article",
        summary="This is a test article summary",
        content_html="<p>Test content</p>",
        content_text="Test content",
        link="https://example.com/article",
        guid="test-guid-123",
        source_url="https://example.com/feed",
        rss_source_id=sample_source.id
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content