from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from slack_sdk.signature import SignatureVerifier

from app.config import get_settings
from app.schemas.slack import DemoCreateTaskResponse, DemoParseRequest
from app.schemas.task import BizOpsTask
from app.services.extraction_service import ExtractionService
from app.services.notion_service import NotionService
from app.services.workflow_service import WorkflowService, parse_demo_message
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/demo/parse", response_model=BizOpsTask)
def demo_parse(payload: DemoParseRequest) -> BizOpsTask:
    return parse_demo_message(payload.message)


@router.post("/demo/create-task", response_model=DemoCreateTaskResponse)
def demo_create_task(payload: DemoParseRequest) -> DemoCreateTaskResponse:
    try:
        task = ExtractionService().extract_task(payload.message)
    except Exception as exc:
        logger.exception("Demo task extraction failed.")
        raise HTTPException(
            status_code=500, detail="Failed to extract task information."
        ) from exc

    try:
        notion_url = NotionService().create_task(task, source_message=payload.message)
    except Exception as exc:
        logger.exception("Demo Notion task creation failed.")
        raise HTTPException(
            status_code=500, detail="Failed to create Notion task."
        ) from exc

    return DemoCreateTaskResponse(task=task, notion_url=notion_url)


@router.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks) -> dict:
    body = await request.body()
    payload = await request.json()

    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    _verify_slack_signature(body=body, request=request)

    if payload.get("type") != "event_callback":
        return {"ok": True}

    event = payload.get("event", {})
    if event.get("type") != "app_mention":
        return {"ok": True}

    # Ignore bot-originated events to avoid accidental loops.
    if event.get("bot_id"):
        return {"ok": True}

    channel = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]
    message = event.get("text", "")

    logger.info("Received Slack app mention in channel %s", channel)
    background_tasks.add_task(
        WorkflowService().process_slack_request,
        channel=channel,
        thread_ts=thread_ts,
        message=message,
    )
    return {"ok": True}


def _verify_slack_signature(body: bytes, request: Request) -> None:
    settings = get_settings()
    if not settings.slack_signing_secret:
        raise HTTPException(
            status_code=500, detail="SLACK_SIGNING_SECRET is not configured."
        )

    verifier = SignatureVerifier(settings.slack_signing_secret)
    if not verifier.is_valid_request(body.decode("utf-8"), request.headers):
        raise HTTPException(status_code=401, detail="Invalid Slack signature.")
