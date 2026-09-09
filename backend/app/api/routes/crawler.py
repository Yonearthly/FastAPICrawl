from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.db.models import CrawlRun
from app.schemas.crawler import CrawlRunOut, SchedulerStatus
from app.services.crawler import run_crawl
from app.services.scheduler import scheduler_status

router = APIRouter(prefix="/crawler", tags=["爬虫管理"])


@router.post("/run", response_model=CrawlRunOut)
async def trigger_crawl(_: AdminUser) -> CrawlRun:
    return await run_crawl(trigger="manual")


@router.get("/runs", response_model=list[CrawlRunOut])
def list_crawl_runs(
    db: DbSession,
    _: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[CrawlRun]:
    return list(
        db.scalars(select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(limit)).all()
    )


@router.get("/scheduler", response_model=SchedulerStatus)
def get_scheduler_status(_: AdminUser) -> dict:
    return scheduler_status()
