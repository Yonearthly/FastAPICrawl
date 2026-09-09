import hashlib
import math
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, CurrentUser, DbSession, OptionalUser
from app.core.cache import cache
from app.db.models import BrowseHistory, CrawlRun, Favorite, News, User, utcnow
from app.schemas.news import (
    DashboardStats,
    FavoriteOut,
    HistoryOut,
    NewsCreate,
    NewsOut,
    NewsPage,
    NewsUpdate,
)
from app.services.crawler import canonicalize_url
from app.services.llm import LLMConfigurationError, LLMServiceError, summarize_news

router = APIRouter(prefix="/news", tags=["新闻"])


def _as_news_out(news: News, favorite: bool = False) -> NewsOut:
    value = NewsOut.model_validate(news)
    return value.model_copy(update={"is_favorite": favorite})


def _favorite_ids(db: DbSession, user: User | None, news_ids: list[int]) -> set[int]:
    if not user or not news_ids:
        return set()
    return set(
        db.scalars(
            select(Favorite.news_id).where(
                Favorite.user_id == user.id, Favorite.news_id.in_(news_ids)
            )
        ).all()
    )


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: DbSession) -> DashboardStats:
    latest_crawl = db.scalar(select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(1))
    return DashboardStats(
        news_count=db.scalar(select(func.count(News.id))) or 0,
        category_count=db.scalar(select(func.count(func.distinct(News.category)))) or 0,
        user_count=db.scalar(select(func.count(User.id))) or 0,
        favorite_count=db.scalar(select(func.count(Favorite.id))) or 0,
        total_views=db.scalar(select(func.sum(News.click_count))) or 0,
        latest_crawl_at=latest_crawl.finished_at if latest_crawl else None,
        latest_crawl_status=latest_crawl.status if latest_crawl else None,
    )


@router.get("/categories", response_model=list[str])
def list_categories(db: DbSession) -> list[str]:
    return list(db.scalars(select(News.category).distinct().order_by(News.category)).all())


@router.get("/recommendations", response_model=list[NewsOut])
def recommendations(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=30)] = 10,
) -> list[NewsOut]:
    preferences = db.execute(
        select(News.category, func.count(BrowseHistory.id).label("views"))
        .join(BrowseHistory, BrowseHistory.news_id == News.id)
        .where(BrowseHistory.user_id == user.id)
        .group_by(News.category)
        .order_by(desc("views"))
        .limit(3)
    ).all()
    preferred_categories = [row.category for row in preferences]
    statement = select(News).where(News.is_published.is_(True))
    if preferred_categories:
        statement = statement.where(News.category.in_(preferred_categories))
    items = list(
        db.scalars(statement.order_by(News.published_at.desc(), News.id.desc()).limit(limit)).all()
    )
    favorite_ids = _favorite_ids(db, user, [item.id for item in items])
    return [_as_news_out(item, item.id in favorite_ids) for item in items]


@router.get("/favorites", response_model=list[FavoriteOut])
def list_favorites(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[FavoriteOut]:
    rows = db.execute(
        select(Favorite, News)
        .join(News, News.id == Favorite.news_id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .limit(limit)
    ).all()
    return [
        FavoriteOut(news=_as_news_out(news, True), created_at=favorite.created_at)
        for favorite, news in rows
    ]


@router.get("/history", response_model=list[HistoryOut])
def list_history(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[HistoryOut]:
    rows = db.execute(
        select(BrowseHistory, News)
        .join(News, News.id == BrowseHistory.news_id)
        .where(BrowseHistory.user_id == user.id)
        .order_by(BrowseHistory.viewed_at.desc())
        .limit(limit)
    ).all()
    favorite_ids = _favorite_ids(db, user, [news.id for _, news in rows])
    return [
        HistoryOut(
            news=_as_news_out(news, news.id in favorite_ids),
            viewed_at=history.viewed_at,
            view_count=history.view_count,
        )
        for history, news in rows
    ]


@router.get("", response_model=NewsPage)
def list_news(
    db: DbSession,
    user: OptionalUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 12,
    category: str | None = None,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    sort: Annotated[str, Query(pattern="^(latest|hot)$")] = "latest",
) -> NewsPage:
    cache_key = f"news:list:{page}:{page_size}:{category or '-'}:{keyword or '-'}:{sort}"
    if not user:
        cached = cache.get_json(cache_key)
        if cached:
            return NewsPage.model_validate(cached)

    statement = select(News).where(News.is_published.is_(True))
    count_statement = select(func.count(News.id)).where(News.is_published.is_(True))
    if category:
        statement = statement.where(News.category == category)
        count_statement = count_statement.where(News.category == category)
    if keyword:
        condition = or_(News.title.contains(keyword), News.content.contains(keyword))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    order = (
        (News.click_count.desc(), News.published_at.desc())
        if sort == "hot"
        else (
            News.published_at.desc(),
            News.id.desc(),
        )
    )
    total = db.scalar(count_statement) or 0
    items = list(
        db.scalars(statement.order_by(*order).offset((page - 1) * page_size).limit(page_size)).all()
    )
    favorite_ids = _favorite_ids(db, user, [item.id for item in items])
    result = NewsPage(
        items=[_as_news_out(item, item.id in favorite_ids) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
    if not user:
        cache.set_json(cache_key, result.model_dump(mode="json"))
    return result


@router.post("", response_model=NewsOut, status_code=status.HTTP_201_CREATED)
def create_news(payload: NewsCreate, db: DbSession, _: AdminUser) -> NewsOut:
    normalized_url = canonicalize_url(payload.source_url)
    news = News(
        **payload.model_dump(exclude={"source_url", "published_at"}),
        source_url=normalized_url,
        url_hash=hashlib.sha256(normalized_url.encode()).hexdigest(),
        published_at=payload.published_at or utcnow(),
    )
    db.add(news)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="该来源地址对应的新闻已存在") from exc
    db.refresh(news)
    cache.delete_pattern("news:*")
    return _as_news_out(news)


@router.get("/{news_id}", response_model=NewsOut)
def get_news(news_id: int, db: DbSession, user: OptionalUser) -> NewsOut:
    news = db.get(News, news_id)
    if not news or (not news.is_published and not (user and user.is_admin)):
        raise HTTPException(status_code=404, detail="新闻不存在")

    news.click_count += 1
    is_favorite = False
    if user:
        history = db.scalar(
            select(BrowseHistory).where(
                BrowseHistory.user_id == user.id, BrowseHistory.news_id == news.id
            )
        )
        if history:
            history.viewed_at = utcnow()
            history.view_count += 1
        else:
            db.add(BrowseHistory(user_id=user.id, news_id=news.id))
        is_favorite = (
            db.scalar(
                select(Favorite.id).where(Favorite.user_id == user.id, Favorite.news_id == news.id)
            )
            is not None
        )
    db.commit()
    db.refresh(news)
    return _as_news_out(news, is_favorite)


@router.patch("/{news_id}", response_model=NewsOut)
def update_news(news_id: int, payload: NewsUpdate, db: DbSession, _: AdminUser) -> NewsOut:
    news = db.get(News, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(news, key, value)
    db.commit()
    db.refresh(news)
    cache.delete_pattern("news:*")
    return _as_news_out(news)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news_id: int, db: DbSession, _: AdminUser) -> None:
    news = db.get(News, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    db.delete(news)
    db.commit()
    cache.delete_pattern("news:*")


@router.post("/{news_id}/favorite", status_code=status.HTTP_201_CREATED)
def favorite_news(news_id: int, db: DbSession, user: CurrentUser) -> dict[str, str]:
    if not db.get(News, news_id):
        raise HTTPException(status_code=404, detail="新闻不存在")
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.news_id == news_id)
    )
    if not existing:
        db.add(Favorite(user_id=user.id, news_id=news_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"message": "已收藏"}


@router.delete("/{news_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def unfavorite_news(news_id: int, db: DbSession, user: CurrentUser) -> None:
    favorite = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.news_id == news_id)
    )
    if favorite:
        db.delete(favorite)
        db.commit()


@router.post("/{news_id}/ai-summary", response_model=NewsOut)
async def generate_ai_summary(news_id: int, db: DbSession, user: CurrentUser) -> NewsOut:
    news = db.get(News, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    try:
        news.ai_summary = await summarize_news(news.title, news.content)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    db.commit()
    db.refresh(news)
    cache.delete_pattern("news:*")
    favorite = (
        db.scalar(
            select(Favorite.id).where(Favorite.user_id == user.id, Favorite.news_id == news.id)
        )
        is not None
    )
    return _as_news_out(news, favorite)
