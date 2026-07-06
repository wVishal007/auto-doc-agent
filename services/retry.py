import time
import random
from typing import Callable, TypeVar

from services.performance import tracker

T = TypeVar("T")


def _is_transient_error(e: Exception) -> bool:
    msg = str(e).lower()
    status_codes = ["429", "500", "502", "503", "504"]
    return (any(code in msg for code in status_codes)
            or "timeout" in msg
            or "rate limit" in msg
            or "empty llm response" in msg)


def _get_exception_label(e: Exception) -> str:
    msg = str(e).lower()
    if "429" in msg:
        return "429 Too Many Requests"
    if "503" in msg:
        return "503 Service Unavailable"
    if "500" in msg:
        return "500 Internal Server Error"
    if "502" in msg:
        return "502 Bad Gateway"
    if "504" in msg:
        return "504 Gateway Timeout"
    if "timeout" in msg:
        return "Timeout"
    if "rate limit" in msg:
        return "Rate Limit"
    return str(e).split("\n")[0][:80]


def invoke_with_retry(
    fn: Callable[[], T],
    max_retries: int = 2,
    label: str = "",
    max_delay: float = 6.0,
) -> T:
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exception = e
            if not _is_transient_error(e):
                raise
            if attempt < max_retries:
                reason = _get_exception_label(e)
                delay = min(max_delay, (2 ** attempt) * 1.0 + random.uniform(0, 0.5))
                tracker.retry(attempt + 1, reason, delay, label)
                time.sleep(delay)
    raise last_exception
