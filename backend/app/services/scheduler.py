from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.services.crawler import run_crawl

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def start_scheduler() -> None:
    if not settings.crawler_enabled or scheduler.running:
        return
    scheduler.add_job(
        run_crawl,
        "interval",
        minutes=settings.crawler_interval_minutes,
        id="sina-news-crawler",
        kwargs={"trigger": "scheduled"},
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        jitter=min(30, max(0, settings.crawler_interval_minutes * 2)),
        next_run_time=datetime.now() + timedelta(seconds=8),
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def scheduler_status() -> dict:
    job = scheduler.get_job("sina-news-crawler") if scheduler.running else None
    return {
        "enabled": settings.crawler_enabled,
        "running": scheduler.running,
        "interval_minutes": settings.crawler_interval_minutes,
        "next_run_at": job.next_run_time if job else None,
    }
