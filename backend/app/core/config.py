from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI掘金头条"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite:///./data/news.db"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    openai_base_url: str = "https://api.openai-proxy.org/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60.0

    crawler_enabled: bool = True
    crawler_interval_minutes: int = 30
    crawler_max_articles: int = 30
    crawler_request_delay_seconds: float = 0.8
    crawler_start_urls: Annotated[list[str], NoDecode] = [
        "https://news.sina.com.cn/",
        "https://news.sina.com.cn/china/",
        "https://news.sina.com.cn/world/",
    ]
    crawler_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126 Safari/537.36 AI-News-Training-Bot/1.0"
    )
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("crawler_start_urls", "cors_origins", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("openai_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
