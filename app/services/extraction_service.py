from pathlib import Path

from app.clients.openai_client import get_openai_client
from app.config import get_settings
from app.schemas.task import BizOpsTask
from app.utils.api_usage import (
    record_mock_extraction_call,
    record_openai_extraction_call,
)
from app.utils.logger import setup_logger

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "task_extraction.txt"
logger = setup_logger(__name__)


class ExtractionService:
    """Turns unstructured Slack text into a validated BizOpsTask."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.instructions = PROMPT_PATH.read_text(encoding="utf-8")

    def extract_task(self, message: str) -> BizOpsTask:
        if self._should_use_mock_extraction():
            record_mock_extraction_call()
            if self.settings.debug_mode:
                logger.info("DEBUG_MODE: returning mock BizOpsTask without OpenAI.")
            return self._mock_task(message)

        client = get_openai_client()
        record_openai_extraction_call()
        response = client.responses.parse(
            model=self.settings.openai_model,
            input=[
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": message},
            ],
            text_format=BizOpsTask,
        )

        if not response.output_parsed:
            raise RuntimeError("OpenAI did not return a parsed BizOpsTask.")

        return response.output_parsed

    def _should_use_mock_extraction(self) -> bool:
        return self.settings.mock_mode or not self.settings.allow_openai_calls

    def _mock_task(self, message: str) -> BizOpsTask:
        lowered_message = message.lower()

        customer = "Acme Corp" if "acme" in lowered_message else None
        assignee = "Alex" if "alex" in lowered_message else None

        return BizOpsTask(
            title="Acme Corp login button not working on Chrome"
            if customer
            else "Operational request from Slack",
            priority="Urgent" if "urgent" in lowered_message else "Medium",
            category="Frontend Bug"
            if "button" in lowered_message or "chrome" in lowered_message
            else "Other",
            assignee=assignee,
            customer=customer,
            summary=(
                "Acme Corp reported that the login button is not working on Chrome, "
                "preventing dashboard access before an upcoming board meeting."
                if customer
                else "A Slack user submitted an operational request for BizOps follow-up."
            ),
            recommended_action=(
                "Create a frontend bug ticket and assign it to Alex."
                if assignee
                else "Review the request and route it to the appropriate owner."
            ),
        )
