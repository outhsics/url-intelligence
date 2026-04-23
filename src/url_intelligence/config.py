from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    ai_provider: str = Field(default="openai", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.4-mini", alias="OPENAI_MODEL")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    anthropic_auth_token: str | None = Field(default=None, alias="ANTHROPIC_AUTH_TOKEN")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL")
    anthropic_base_url: str | None = Field(default=None, alias="ANTHROPIC_BASE_URL")
    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")
    cache_ttl_seconds: int = Field(default=21600, alias="CACHE_TTL_SECONDS")
    cache_dir: Path = Field(default=Path(".cache/url-intelligence"))

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")


settings = Settings()
