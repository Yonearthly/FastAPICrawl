from fastapi import APIRouter

from app.api.routes import auth, crawler, news

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(news.router)
api_router.include_router(crawler.router)
