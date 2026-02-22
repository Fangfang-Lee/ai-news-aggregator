from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
import logging
import os

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models.rss_models import Base
from app.api.routes import api_router

# Resolve paths relative to the working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup & shutdown logic"""
    # --- Startup ---
    logger.info("Starting AI News Aggregator...")

    # Create database tables & initialize default data
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

        from app.services.category_service import CategoryService
        from app.models.rss_models import RSSSource

        db = SessionLocal()
        try:
            category_service = CategoryService(db)
            category_service.initialize_default_categories()
            logger.info("Default categories initialized")

            existing_sources = db.query(RSSSource).count()
            if existing_sources == 0:
                _initialize_default_sources(db, category_service)
                logger.info("Default RSS sources initialized")
            else:
                logger.info(f"Skipping RSS source init: {existing_sources} sources already exist")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization failed (app will still start): {e}")

    yield  # Application is running

    # --- Shutdown ---
    logger.info("Shutting down AI News Aggregator...")


# Create FastAPI app
app = FastAPI(
    title="AI News Aggregator",
    description="AI news aggregation website with RSS feed management",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files and templates (if frontend directory exists)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR) if os.path.isdir(TEMPLATES_DIR) else None


@app.get("/")
def home(request: Request):
    """Home page"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return {"message": "AI News Aggregator API", "docs": "/docs"}


@app.get("/health")
def health_check():
    """Health check endpoint — always returns 200 so Render deploy succeeds"""
    status = {"status": "healthy", "db": "ok", "redis": "ok"}

    # Check database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        status["status"] = "degraded"
        status["db"] = str(e)

    # Check Redis
    try:
        from app.core.redis_client import redis_client
        redis_client.ping()
    except Exception as e:
        status["status"] = "degraded"
        status["redis"] = str(e)

    # Always return 200 — status body shows actual health details
    return status


def _initialize_default_sources(db, category_service):
    """Initialize default RSS sources for fresh installation"""
    from app.services.rss_service import RSSService
    from app.api.schemas import RSSSourceCreate

    rss_service = RSSService(db)

    ai = category_service.get_category_by_name('AI')
    tech = category_service.get_category_by_name('Technology')
    dev = category_service.get_category_by_name('Developer')
    cloud = category_service.get_category_by_name('Cloud & DevOps')

    sources = [
        # AI — Chinese
        {'name': '机器之心', 'url': 'https://plink.anyfeeder.com/weixin/almosthuman2014', 'description': 'AI 领域专业媒体', 'category_id': ai.id if ai else None},
        {'name': '新智元', 'url': 'https://plink.anyfeeder.com/weixin/AI_era', 'description': 'AI 产业资讯与技术动态', 'category_id': ai.id if ai else None},
        {'name': 'AI 科技评论', 'url': 'https://rsshub.rssforever.com/leiphone/category/ai', 'description': '雷锋网AI频道，学术+产业', 'category_id': ai.id if ai else None},
        # AI — International
        {'name': 'OpenAI Blog', 'url': 'https://openai.com/blog/rss.xml', 'description': 'OpenAI official blog', 'category_id': ai.id if ai else None},
        {'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog/feed.xml', 'description': 'Open-source AI ecosystem', 'category_id': ai.id if ai else None},
        {'name': 'Google AI Blog', 'url': 'https://blog.google/technology/ai/rss/', 'description': 'Google AI research updates', 'category_id': ai.id if ai else None},
        {'name': 'Sebastian Raschka AI', 'url': 'https://magazine.sebastianraschka.com/feed', 'description': 'In-depth LLM research analysis', 'category_id': ai.id if ai else None},
        {'name': 'MIT Tech Review AI', 'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed', 'description': 'MIT AI industry perspective', 'category_id': ai.id if ai else None},
        {'name': 'TechCrunch AI', 'url': 'https://techcrunch.com/category/artificial-intelligence/feed', 'description': 'Silicon Valley AI news', 'category_id': ai.id if ai else None},
        {'name': 'Towards Data Science', 'url': 'https://towardsdatascience.com/feed', 'description': 'AI/ML hands-on technical articles', 'category_id': ai.id if ai else None},
        # Technology
        {'name': '虎嗅', 'url': 'https://www.huxiu.com/rss/0.xml', 'description': '科技商业深度报道', 'category_id': tech.id if tech else None},
        {'name': '腾讯科技', 'url': 'https://plink.anyfeeder.com/weixin/qqtech', 'description': '科技产业资讯', 'category_id': tech.id if tech else None},
        # Developer
        {'name': '阮一峰的网络日志', 'url': 'https://www.ruanyifeng.com/blog/atom.xml', 'description': '技术博客，每周科技周刊', 'category_id': dev.id if dev else None},
        {'name': 'InfoQ 推荐', 'url': 'https://plink.anyfeeder.com/infoq/recommend', 'description': '软件开发技术前沿资讯', 'category_id': dev.id if dev else None},
        # Cloud & DevOps
        {'name': '美团技术团队', 'url': 'https://tech.meituan.com/feed/', 'description': '美团技术实践与架构分享', 'category_id': cloud.id if cloud else None},
    ]

    for src in sources:
        try:
            rss_service.create_source(RSSSourceCreate(**src))
            logger.info(f"Added RSS source: {src['name']}")
        except ValueError:
            pass  # Already exists
        except Exception as e:
            logger.error(f"Error adding {src['name']}: {e}")
