from dataclasses import dataclass
from threading import Lock

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ApiUsage:
    openai_extraction_calls: int = 0
    mock_extraction_calls: int = 0


_usage = ApiUsage()
_lock = Lock()


def record_openai_extraction_call() -> int:
    """Record one real OpenAI extraction call and return the cumulative count."""

    with _lock:
        _usage.openai_extraction_calls += 1
        count = _usage.openai_extraction_calls

    logger.info("OpenAI extraction API calls made in this process: %s", count)
    return count


def record_mock_extraction_call() -> int:
    """Record one mock extraction for local cost-free development."""

    with _lock:
        _usage.mock_extraction_calls += 1
        count = _usage.mock_extraction_calls

    logger.info("Mock extraction calls made in this process: %s", count)
    return count


def get_usage_snapshot() -> ApiUsage:
    with _lock:
        return ApiUsage(
            openai_extraction_calls=_usage.openai_extraction_calls,
            mock_extraction_calls=_usage.mock_extraction_calls,
        )
