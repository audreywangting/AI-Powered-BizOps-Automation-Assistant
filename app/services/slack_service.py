import certifi
import httpx

from app.config import get_settings
from app.schemas.task import BizOpsTask


class SlackPostError(RuntimeError):
    """Raised when Slack rejects or fails a chat.postMessage call."""


class SlackService:
    """Posts threaded Slack updates for the local MVP workflow."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.slack_bot_token:
            raise RuntimeError("SLACK_BOT_TOKEN is not configured.")

        self.bot_token = settings.slack_bot_token

    def reply(self, channel: str, thread_ts: str, text: str) -> None:
        # Use httpx + certifi instead of the Slack SDK urllib transport. This
        # avoids macOS framework Python installs with a missing OpenSSL CA file.
        response = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"channel": channel, "thread_ts": thread_ts, "text": text},
            timeout=10,
            verify=certifi.where(),
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise SlackPostError(f"Slack chat.postMessage failed: {error_code}")

    def reply_task_created(
        self, channel: str, thread_ts: str, task: BizOpsTask, notion_url: str
    ) -> None:
        message = (
            "✅ Task successfully created.\n\n"
            f"Title: {task.title}\n\n"
            f"Priority: {task.priority}\n\n"
            f"Category: {task.category}\n\n"
            f"Assignee: {task.assignee or 'Unassigned'}\n\n"
            f"View Task: {notion_url or 'Created in Notion'}"
        )
        self.reply(channel=channel, thread_ts=thread_ts, text=message)

    def reply_error(self, channel: str, thread_ts: str, text: str) -> None:
        try:
            self.reply(channel=channel, thread_ts=thread_ts, text=text)
        except Exception:
            # Avoid hiding the original workflow error with a Slack follow-up error.
            pass
