from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CrawlRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trigger: str
    status: str
    discovered_count: int
    new_count: int
    skipped_count: int
    failed_count: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class SchedulerStatus(BaseModel):
    enabled: bool
    running: bool
    interval_minutes: int
    next_run_at: datetime | None
