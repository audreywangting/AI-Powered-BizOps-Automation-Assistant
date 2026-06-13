import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.services.extraction_service import ExtractionService  # noqa: E402

BENCHMARK_DIR = Path(__file__).resolve().parent
REQUESTS_PATH = BENCHMARK_DIR / "mock_requests.json"
LABELS_PATH = BENCHMARK_DIR / "golden_labels.json"
RESULTS_PATH = BENCHMARK_DIR / "results.json"
SETUP_ERROR_PATTERNS = ("connection error", "api key", "authentication", "rate limit")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip().lower()
    return cleaned or None


def accuracy(correct: int, total: int) -> float:
    return round(correct / total, 4) if total else 0.0


def main() -> None:
    requests = load_json(REQUESTS_PATH)
    labels_by_id = {item["id"]: item for item in load_json(LABELS_PATH)}

    settings = get_settings()
    extraction_mode = (
        "openai"
        if settings.allow_openai_calls and not settings.mock_mode
        else "mock"
    )

    extractor = ExtractionService()
    total = len(requests)
    successes = 0
    priority_correct = 0
    category_correct = 0
    assignee_correct = 0
    latencies: list[int] = []
    stopped_early = False
    stop_reason = None

    for item in requests:
        request_id = item["id"]
        raw_message = item["raw_message"]
        expected = labels_by_id[request_id]

        started_at = perf_counter()
        prediction = None
        error = None

        try:
            prediction = extractor.extract_task(raw_message)
            successes += 1
        except Exception as exc:
            error = str(exc)

        latency_ms = int((perf_counter() - started_at) * 1000)
        latencies.append(latency_ms)

        priority_match = bool(
            prediction and prediction.priority == expected["expected_priority"]
        )
        category_match = bool(
            prediction and prediction.category == expected["expected_category"]
        )
        assignee_match = bool(
            prediction
            and normalize_text(prediction.assignee)
            == normalize_text(expected["expected_assignee"])
        )

        priority_correct += int(priority_match)
        category_correct += int(category_match)
        assignee_correct += int(assignee_match)

        if (
            extraction_mode == "openai"
            and error
            and any(pattern in error.lower() for pattern in SETUP_ERROR_PATTERNS)
        ):
            stopped_early = True
            stop_reason = error
            break

    results = {
        "num_requests": total,
        "attempted_requests": len(latencies),
        "success_rate": accuracy(successes, total),
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
        "priority_accuracy": accuracy(priority_correct, total),
        "category_accuracy": accuracy(category_correct, total),
        "assignee_accuracy": accuracy(assignee_correct, total),
        "extraction_mode": extraction_mode,
        "stopped_early": stopped_early,
        "stop_reason": stop_reason,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
