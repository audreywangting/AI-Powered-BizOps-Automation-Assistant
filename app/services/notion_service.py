from typing import Any, Dict, Optional

from app.clients.notion_client import get_notion_client
from app.config import get_settings
from app.schemas.task import BizOpsTask


class NotionService:
    """Creates Notion pages for extracted BizOps tasks."""

    # Keep Notion database property names configurable in one obvious place.
    FIELD_MAP = {
        "title": "Title",
        "priority": "Priority",
        "category": "Category",
        "assignee": "Assignee",
        "customer": "Customer",
        "summary": "Summary",
        "recommended_action": "Recommended Action",
        "status": "Status",
        "source_message": "Source Message",
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()
        if not self.settings.notion_database_id:
            raise RuntimeError("NOTION_DATABASE_ID is not configured.")

    def create_task(self, task: BizOpsTask, source_message: str) -> str:
        response = self.client.pages.create(
            parent={"database_id": self.settings.notion_database_id},
            properties=self._build_properties(task, source_message),
        )
        return response.get("url", "")

    def _build_properties(
        self, task: BizOpsTask, source_message: str
    ) -> Dict[str, Dict[str, Any]]:
        return {
            self.FIELD_MAP["title"]: self._title(task.title),
            self.FIELD_MAP["priority"]: self._select(task.priority),
            self.FIELD_MAP["category"]: self._select(task.category),
            self.FIELD_MAP["assignee"]: self._rich_text(task.assignee),
            self.FIELD_MAP["customer"]: self._rich_text(task.customer),
            self.FIELD_MAP["summary"]: self._rich_text(task.summary),
            self.FIELD_MAP["recommended_action"]: self._rich_text(
                task.recommended_action
            ),
            self.FIELD_MAP["status"]: self._select("Not Started"),
            self.FIELD_MAP["source_message"]: self._rich_text(source_message),
        }

    def _title(self, value: str) -> Dict[str, Any]:
        return {"title": [{"text": {"content": value[:2000]}}]}

    def _select(self, value: str) -> Dict[str, Any]:
        return {"select": {"name": value}}

    def _rich_text(self, value: Optional[str]) -> Dict[str, Any]:
        text = value or ""
        return {"rich_text": [{"text": {"content": text[:2000]}}]} if text else {"rich_text": []}
