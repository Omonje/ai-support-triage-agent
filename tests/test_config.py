import pytest

from app.config import load_settings
from app.errors import ConfigError


def test_loads_with_all_required_vars_set(required_env):
    settings = load_settings(env_file=None)
    assert settings.anthropic_api_key == "test-key"
    assert settings.monday_board_id == "123456"
    assert settings.gmail_label == "Triage-Demo"
    assert settings.confidence_escalation_threshold == 0.6
    assert settings.llm_provider == "claude"


def test_defaults_to_claude_and_does_not_require_a_google_key(required_env):
    settings = load_settings(env_file=None)
    assert settings.llm_provider == "claude"
    assert settings.google_api_key == ""


def test_gemini_provider_requires_google_api_key_not_anthropic(required_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("ANTHROPIC_API_KEY")

    with pytest.raises(ConfigError, match="GOOGLE_API_KEY"):
        load_settings(env_file=None)

    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    settings = load_settings(env_file=None)
    assert settings.llm_provider == "gemini"
    assert settings.google_api_key == "test-google-key"


def test_groq_provider_requires_groq_api_key_not_anthropic(required_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("ANTHROPIC_API_KEY")

    with pytest.raises(ConfigError, match="GROQ_API_KEY"):
        load_settings(env_file=None)

    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    settings = load_settings(env_file=None)
    assert settings.llm_provider == "groq"
    assert settings.groq_api_key == "test-groq-key"


def test_slack_webhook_url_is_optional_and_defaults_to_empty(required_env):
    settings = load_settings(env_file=None)
    assert settings.slack_webhook_url == ""


def test_slack_webhook_url_is_picked_up_when_set(required_env, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.test/abc")
    settings = load_settings(env_file=None)
    assert settings.slack_webhook_url == "https://hooks.slack.test/abc"


def test_fails_fast_on_unknown_llm_provider(required_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(ConfigError, match="LLM_PROVIDER"):
        load_settings(env_file=None)


def test_fails_fast_when_a_required_var_is_missing(required_env, monkeypatch):
    monkeypatch.delenv("MONDAY_API_TOKEN")
    with pytest.raises(ConfigError, match="MONDAY_API_TOKEN"):
        load_settings(env_file=None)


def test_fails_fast_when_supabase_url_is_missing(required_env, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL")
    with pytest.raises(ConfigError, match="SUPABASE_URL"):
        load_settings(env_file=None)


def test_loads_supabase_settings(required_env):
    settings = load_settings(env_file=None)
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_service_key == "test-supabase-key"


def test_fails_fast_on_out_of_range_threshold(required_env, monkeypatch):
    monkeypatch.setenv("CONFIDENCE_ESCALATION_THRESHOLD", "1.5")
    with pytest.raises(ConfigError, match="between 0 and 1"):
        load_settings(env_file=None)


def test_fails_fast_on_non_numeric_threshold(required_env, monkeypatch):
    monkeypatch.setenv("CONFIDENCE_ESCALATION_THRESHOLD", "not-a-number")
    with pytest.raises(ConfigError, match="must be a number"):
        load_settings(env_file=None)
