from fastapi import APIRouter

from app.utils.api_usage import get_usage_snapshot

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/debug/usage")
def api_usage() -> dict[str, int]:
    usage = get_usage_snapshot()
    return {
        "openai_extraction_calls": usage.openai_extraction_calls,
        "mock_extraction_calls": usage.mock_extraction_calls,
    }
