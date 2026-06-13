import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from app.schemas.task import BizOpsTask
from app.utils.logger import setup_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = PROJECT_ROOT / "telemetry"
WORKFLOW_LOG_PATH = TELEMETRY_DIR / "workflow_logs.jsonl"

logger = setup_logger(__name__)
_write_lock = Lock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_workflow_log(
    *,
    request_id: str,
    timestamp: str,
    success: bool,
    latency_ms: int,
    task: Optional[BizOpsTask],
    notion_created: bool,
) -> None:
    """Append one workflow telemetry event as JSONL."""

    event: dict[str, Any] = {
        "request_id": request_id,
        "timestamp": timestamp,
        "success": success,
        "latency_ms": latency_ms,
        "priority": task.priority if task else None,
        "category": task.category if task else None,
        "assignee_extracted": bool(task and task.assignee),
        "notion_created": notion_created,
    }

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with WORKFLOW_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event) + "\n")

    logger.info("Workflow telemetry logged for request_id=%s", request_id)
