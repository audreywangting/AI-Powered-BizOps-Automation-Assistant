from notion_client import Client

from app.config import get_settings


def get_notion_client() -> Client:
    settings = get_settings()
    if not settings.notion_api_key:
        raise RuntimeError("NOTION_API_KEY is not configured.")

    return Client(auth=settings.notion_api_key)
