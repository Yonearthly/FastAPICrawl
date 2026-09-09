import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.cache import cache
from app.core.config import settings
from app.db.session import Base, engine
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    description=("新浪新闻定时采集、去重入库、Redis 缓存、JWT 用户体系、收藏历史与 AI 摘要接口。"),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["系统"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "status": "running"}


@app.get("/health", tags=["系统"])
def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": "connected",
        "redis": "connected" if cache.ping() else "unavailable",
        "scheduler_enabled": settings.crawler_enabled,
        "llm_configured": bool(settings.openai_api_key),
        "llm_base_url": settings.openai_base_url,
    }
