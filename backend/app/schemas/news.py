from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsCreate(BaseModel):
    title: str = Field(min_length=2, max_length=500)
    content: str = Field(min_length=2)
    description: str | None = None
    category: str = Field(default="综合", max_length=50)
    source_name: str = Field(default="手动发布", max_length=50)
    source_author: str | None = Field(default=None, max_length=120)
    source_url: str = Field(min_length=4, max_length=700)
    image_url: str | None = Field(default=None, max_length=1000)
    published_at: datetime | None = None
    is_published: bool = True


class NewsUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=500)
    content: str | None = Field(default=None, min_length=2)
    description: str | None = None
    category: str | None = Field(default=None, max_length=50)
    image_url: str | None = Field(default=None, max_length=1000)
    is_published: bool | None = None


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    description: str | None
    ai_summary: str | None
    category: str
    source_name: str
    source_author: str | None
    source_url: str
    image_url: str | None
    published_at: datetime | None
    crawled_at: datetime
    updated_at: datetime
    click_count: int
    is_published: bool
    is_favorite: bool = False


class NewsPage(BaseModel):
    items: list[NewsOut]
    total: int
    page: int
    page_size: int
    pages: int


class FavoriteOut(BaseModel):
    news: NewsOut
    created_at: datetime


class HistoryOut(BaseModel):
    news: NewsOut
    viewed_at: datetime
    view_count: int


class DashboardStats(BaseModel):
    news_count: int
    category_count: int
    user_count: int
    favorite_count: int
    total_views: int
    latest_crawl_at: datetime | None
    latest_crawl_status: str | None
