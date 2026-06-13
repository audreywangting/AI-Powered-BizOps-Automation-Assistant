from time import perf_counter
from uuid import uuid4

from app.schemas.task import BizOpsTask
from app.services.extraction_service import ExtractionService
from app.services.notion_service import NotionService
from app.services.slack_service import SlackService
from app.utils.logger import setup_logger
from app.utils.telemetry import append_workflow_log, utc_now_iso

logger = setup_logger(__name__)


class WorkflowService:
    """Coordinates Slack confirmation, extraction, validation, and Notion creation."""

    def __init__(self) -> None:
        self.slack = SlackService()

    def process_slack_request(self, channel: str, thread_ts: str, message: str) -> None:
        request_id = str(uuid4())
        started_at = perf_counter()
        timestamp = utc_now_iso()
        success = False
        notion_created = False
        task: BizOpsTask | None = None

        try:
            self.slack.reply(
                channel=channel,
                thread_ts=thread_ts,
                text="👀 Parsing request and creating a Notion task...",
            )

            try:
                task = ExtractionService().extract_task(message)
                logger.info("Extracted task: %s", task.model_dump())
            except Exception:
                logger.exception("OpenAI extraction failed.")
                self.slack.reply_error(
                    channel=channel,
                    thread_ts=thread_ts,
                    text="❌ Failed to extract task information.",
                )
                return

            try:
                notion_url = NotionService().create_task(
                    task=task, source_message=message
                )
                notion_created = True
                logger.info("Created Notion task: %s", notion_url)
            except Exception:
                logger.exception("Notion task creation failed.")
                self.slack.reply_error(
                    channel=channel,
                    thread_ts=thread_ts,
                    text="❌ Failed to create Notion task.",
                )
                return

            self.slack.reply_task_created(
                channel=channel, thread_ts=thread_ts, task=task, notion_url=notion_url
            )
            success = True
        except Exception:
            logger.exception("Workflow failed before completion.")
        finally:
            latency_ms = int((perf_counter() - started_at) * 1000)
            append_workflow_log(
                request_id=request_id,
                timestamp=timestamp,
                success=success,
                latency_ms=latency_ms,
                task=task,
                notion_created=notion_created,
            )


def parse_demo_message(message: str) -> BizOpsTask:
    return ExtractionService().extract_task(message)
