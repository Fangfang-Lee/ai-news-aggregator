from fastapi import APIRouter
from app.api.routes import sources, categories, content, cron

api_router = APIRouter()

api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"])