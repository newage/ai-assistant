from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(min_length=1)
    claude_model: str = "claude-haiku-5-5"
    claude_effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None
    qdrant_url: str = "http://vector-db:6333"
    faq_collection: str = "faq"
    faq_top_k: int = 4
    mcp_url: str = "http://mcp-server:9501/mcp"
    max_messages: int = 50

    @field_validator("claude_effort", mode="before")
    @classmethod
    def _empty_effort_is_unset(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


@lru_cache
def get_settings() -> Settings:
    return Settings()
