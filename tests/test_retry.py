import pytest

from app.gateways.retry import retry_with_backoff


def test_returns_the_result_on_first_success():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result = retry_with_backoff(fn, sleep=lambda seconds: None)

    assert result == "ok"
    assert len(calls) == 1


def test_retries_after_a_failure_and_eventually_succeeds():
    attempts = []

    def fn():
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("transient")
        return "ok"

    result = retry_with_backoff(fn, max_attempts=3, sleep=lambda seconds: None)

    assert result == "ok"
    assert len(attempts) == 3


def test_gives_up_after_max_attempts_and_raises_the_last_error():
    attempts = []

    def fn():
        attempts.append(1)
        raise RuntimeError(f"failure {len(attempts)}")

    with pytest.raises(RuntimeError, match="failure 3"):
        retry_with_backoff(fn, max_attempts=3, sleep=lambda seconds: None)

    assert len(attempts) == 3


def test_sleeps_with_exponential_backoff_between_attempts():
    sleep_calls = []

    def fn():
        raise RuntimeError("always fails")

    with pytest.raises(RuntimeError):
        retry_with_backoff(fn, max_attempts=3, base_delay_seconds=1.0, sleep=sleep_calls.append)

    assert sleep_calls == [1.0, 2.0]
