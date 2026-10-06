"""Retry a transient outside-call failure with exponential backoff
(1s, 2s, 4s, ...). Used by the LLM gateways around their API calls, since
provider outages are usually brief (see DECISIONS.md / TESTS.md risk:
"Claude/Gemini API down or slow"). Does not inspect the exception type,
every failure is treated as potentially transient and retried up to
max_attempts before being re-raised as-is."""

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                sleep(base_delay_seconds * (2**attempt))

    raise last_exc
