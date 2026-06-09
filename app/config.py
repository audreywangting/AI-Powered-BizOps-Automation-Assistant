from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"
    allow_openai_calls: bool = False
    mock_mode: bool = True
    debug_mode: bool = False

    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None

    notion_api_key: Optional[str] = None
    notion_database_id: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
