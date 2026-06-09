from slack_sdk import WebClient

from app.config import get_settings


def get_slack_client() -> WebClient:
    settings = get_settings()
    if not settings.slack_bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is not configured.")

    return WebClient(token=settings.slack_bot_token)
