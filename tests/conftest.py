import pytest


@pytest.fixture
def required_env(monkeypatch):
    """The minimum env vars load_settings() needs. Individual tests can
    unset one to check the fail-fast behaviour."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("MONDAY_API_TOKEN", "test-token")
    monkeypatch.setenv("MONDAY_BOARD_ID", "123456")
