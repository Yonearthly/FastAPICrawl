import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.cache import cache
from app.core.config import settings
from app.db.models import CrawlRun, News, utcnow
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
crawl_lock = asyncio.Lock()

TRACKING_PARAMS = {"from", "froms", "pos", "cre", "mod", "loc", "r", "wm", "vt", "cid"}


@dataclass
class ParsedArticle:
    title: str
    content: str
    description: str | None
    category: str
    source_author: str | None
    image_url: str | None
    published_at: datetime | None


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    host = (parts.hostname or "").lower()
    if host.startswith("www.") and host != "www.sina.com.cn":
        host = host[4:]
    port = parts.port
    netloc = (
        host if not port or (scheme, port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    )
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query)
            if key.lower() not in TRACKING_PARAMS
        )
    )
    return urlunsplit((scheme, netloc, path, query, ""))


def url_fingerprint(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()


def is_sina_article_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    path = parts.path.lower()
    if not host.endswith("sina.com.cn") or not path.endswith((".shtml", ".html")):
        return False
    return bool(re.search(r"/(?:19|20)\d{2}-\d{2}-\d{2}/", path) and "doc-" in path)


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        node = soup.select_one(f'meta[property="{name}"]') or soup.select_one(
            f'meta[name="{name}"]'
        )
        if node and node.get("content"):
            return str(node["content"]).strip()
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("T", " ").removesuffix("Z").split("+")[0].strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized[:19], fmt)
        except ValueError:
            continue
    return None


def _infer_category(url: str, soup: BeautifulSoup) -> str:
    explicit = _meta(soup, "article:section", "section")
    if explicit:
        return explicit[:50]
    host = urlsplit(url).hostname or ""
    path = urlsplit(url).path
    if host.startswith("mil."):
        return "军事"
    if host.startswith("finance."):
        return "财经"
    if host.startswith("tech."):
        return "科技"
    if re.search(r"/w/|/world/|/zx/gj/", path):
        return "国际"
    if re.search(r"/c/|/china/|/gov/", path):
        return "国内"
    return "综合"


def parse_article(html: str, url: str) -> ParsedArticle | None:
    soup = BeautifulSoup(html, "html.parser")
    title = _meta(soup, "og:title")
    if not title:
        title_node = soup.select_one("h1.main-title, h1#artibodyTitle, h1")
        title = title_node.get_text(" ", strip=True) if title_node else None

    body = soup.select_one("#article, #artibody, .article-body, .article-content")
    paragraphs = body.select("p") if body else soup.select(".article-content p, .main-content p")
    content_parts = []
    for paragraph in paragraphs:
        classes = set(paragraph.get("class", []))
        if classes.intersection({"show_author", "article-editor", "source"}):
            continue
        text = paragraph.get_text(" ", strip=True)
        if len(text) >= 8 and not text.startswith(("责任编辑：", "来源：")):
            content_parts.append(text)
    content = "\n\n".join(dict.fromkeys(content_parts))
    if not title or len(content) < 30:
        return None

    source_node = soup.select_one(".source, .date-source a, #media_name")
    source_author = source_node.get_text(" ", strip=True) if source_node else _meta(soup, "author")
    return ParsedArticle(
        title=title[:500],
        content=content,
        description=_meta(soup, "og:description", "description"),
        category=_infer_category(url, soup),
        source_author=(source_author or "")[:120] or None,
        image_url=_meta(soup, "og:image"),
        published_at=_parse_datetime(
            _meta(soup, "article:published_time", "weibo: article:create_at", "publishdate")
        ),
    )


async def _discover(client: httpx.AsyncClient) -> list[str]:
    urls: list[str] = []
    for start_url in settings.crawler_start_urls:
        try:
            response = await client.get(start_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.select("a[href]"):
                candidate = canonicalize_url(urljoin(start_url, str(link["href"])))
                if is_sina_article_url(candidate) and candidate not in urls:
                    urls.append(candidate)
        except httpx.HTTPError as exc:
            logger.warning("Failed to discover Sina links from %s: %s", start_url, exc)
    return urls


def _known_hashes(db, hashes: list[str]) -> set[str]:
    known: set[str] = set()
    for start in range(0, len(hashes), 500):
        batch = hashes[start : start + 500]
        known.update(db.scalars(select(News.url_hash).where(News.url_hash.in_(batch))).all())
    return known


async def run_crawl(trigger: str = "scheduled") -> CrawlRun:
    db = SessionLocal()
    run = CrawlRun(trigger=trigger, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    if crawl_lock.locked():
        run.status = "skipped"
        run.error_message = "已有爬取任务正在运行"
        run.finished_at = utcnow()
        db.commit()
        db.refresh(run)
        db.close()
        return run

    try:
        async with crawl_lock:
            timeout = httpx.Timeout(20.0, connect=10.0)
            headers = {
                "User-Agent": settings.crawler_user_agent,
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            async with httpx.AsyncClient(
                headers=headers, timeout=timeout, follow_redirects=True
            ) as client:
                discovered = await _discover(client)
                run.discovered_count = len(discovered)
                hashes = [url_fingerprint(url) for url in discovered]
                known = _known_hashes(db, hashes)
                candidates = [url for url in discovered if url_fingerprint(url) not in known]
                run.skipped_count = len(discovered) - len(candidates)

                for url in candidates[: settings.crawler_max_articles]:
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        article = parse_article(response.text, url)
                        if not article:
                            run.failed_count += 1
                            continue
                        news = News(
                            title=article.title,
                            content=article.content,
                            description=article.description,
                            category=article.category,
                            source_name="新浪新闻",
                            source_author=article.source_author,
                            source_url=url,
                            url_hash=url_fingerprint(url),
                            image_url=article.image_url,
                            published_at=article.published_at,
                        )
                        db.add(news)
                        try:
                            db.commit()
                            run.new_count += 1
                        except IntegrityError:
                            db.rollback()
                            run.skipped_count += 1
                    except (httpx.HTTPError, UnicodeError, ValueError) as exc:
                        logger.warning("Failed to crawl %s: %s", url, exc)
                        run.failed_count += 1
                    if settings.crawler_request_delay_seconds > 0:
                        await asyncio.sleep(settings.crawler_request_delay_seconds)

            run.status = "completed"
            cache.delete_pattern("news:*")
    except Exception as exc:
        logger.exception("Crawl run %s failed", run.id)
        run.status = "failed"
        run.error_message = str(exc)[:2000]
    finally:
        run.finished_at = utcnow()
        db.add(run)
        db.commit()
        db.refresh(run)
        db.expunge(run)
        db.close()
    return run
