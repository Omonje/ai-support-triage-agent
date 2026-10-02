import pytest

from app.config import load_settings
from app.errors import ConfigError


def test_loads_with_all_required_vars_set(required_env):
    settings = load_settings(env_file=None)
    assert settings.anthropic_api_key == "test-key"
    assert settings.monday_board_id == "123456"
    assert settings.gmail_label == "Triage-Demo"
    assert settings.confidence_escalation_threshold == 0.6


def test_fails_fast_when_a_required_var_is_missing(required_env, monkeypatch):
    monkeypatch.delenv("MONDAY_API_TOKEN")
    with pytest.raises(ConfigError, match="MONDAY_API_TOKEN"):
        load_settings(env_file=None)


def test_fails_fast_on_out_of_range_threshold(required_env, monkeypatch):
    monkeypatch.setenv("CONFIDENCE_ESCALATION_THRESHOLD", "1.5")
    with pytest.raises(ConfigError, match="between 0 and 1"):
        load_settings(env_file=None)


def test_fails_fast_on_non_numeric_threshold(required_env, monkeypatch):
    monkeypatch.setenv("CONFIDENCE_ESCALATION_THRESHOLD", "not-a-number")
    with pytest.raises(ConfigError, match="must be a number"):
        load_settings(env_file=None)
