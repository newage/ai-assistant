from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(min_length=1)
    claude_model: str = "claude-haiku-5-5"
    claude_effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None
    claude_max_tokens: int = Field(1024, gt=0)  # output cap of every single Claude call
    qdrant_url: str = "http://vector-db:6333"
    faq_collection: str = "faq"
    faq_top_k: int = 4
    max_messages: int = Field(4, gt=0)
    max_message_chars: int = Field(500, gt=0)
    faq_min_score: float = Field(0.82, ge=0, le=1)  # FAQ hits below this similarity are not "data"
    log_id: str = "dev"
    environment: str = "local"

    @field_validator("claude_effort", mode="before")
    @classmethod
    def _empty_effort_is_unset(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


@lru_cache
def get_settings() -> Settings:
    return Settings()
