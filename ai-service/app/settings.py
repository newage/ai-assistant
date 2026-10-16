from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(min_length=1)
    claude_model: str = "claude-sonnet-5-5"
    qdrant_url: str = "http://vector-db:6333"
    faq_collection: str = "faq"
    faq_top_k: int = 4
    mcp_url: str = "http://mcp-server:9501/mcp"
    max_messages: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
