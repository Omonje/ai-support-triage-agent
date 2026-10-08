"""Config is read once at start and checked. A bad or missing value stops
the program immediately with a clear message, never fails silently later
mid-request."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.errors import ConfigError

_ALWAYS_REQUIRED = ["MONDAY_API_TOKEN", "MONDAY_BOARD_ID"]

# Which env var each LLM provider needs. Only the active provider's key
# is required, so swapping providers never needs both configured.
_PROVIDER_KEY_ENV_VAR = {
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
}


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    anthropic_api_key: str
    google_api_key: str
    groq_api_key: str
    gmail_oauth_client_path: str
    gmail_token_cache_path: str
    gmail_label: str
    gmail_processed_label: str
    gmail_escalation_label: str
    monday_api_token: str
    monday_board_id: str
    slack_webhook_url: str
    inbox_poll_interval_seconds: int
    sent_check_poll_interval_seconds: int
    confidence_escalation_threshold: float


def load_settings(env_file: str | None = ".env") -> Settings:
    if env_file:
        load_dotenv(env_file)

    llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
    if llm_provider not in _PROVIDER_KEY_ENV_VAR:
        raise ConfigError(
            f"LLM_PROVIDER must be one of {sorted(_PROVIDER_KEY_ENV_VAR)}, got {llm_provider!r}."
        )

    required = [*_ALWAYS_REQUIRED, _PROVIDER_KEY_ENV_VAR[llm_provider]]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ConfigError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill them in."
        )

    try:
        threshold = float(os.getenv("CONFIDENCE_ESCALATION_THRESHOLD", "0.6"))
    except ValueError as exc:
        raise ConfigError(
            "CONFIDENCE_ESCALATION_THRESHOLD must be a number between 0 and 1."
        ) from exc
    if not 0.0 <= threshold <= 1.0:
        raise ConfigError("CONFIDENCE_ESCALATION_THRESHOLD must be between 0 and 1.")

    return Settings(
        llm_provider=llm_provider,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        gmail_oauth_client_path=os.getenv("GMAIL_OAUTH_CLIENT_PATH", "credentials.json"),
        gmail_token_cache_path=os.getenv("GMAIL_TOKEN_CACHE_PATH", "gmail_token.json"),
        gmail_label=os.getenv("GMAIL_LABEL", "Triage-Demo"),
        gmail_processed_label=os.getenv("GMAIL_PROCESSED_LABEL", "Processed"),
        gmail_escalation_label=os.getenv("GMAIL_ESCALATION_LABEL", "Needs-Human"),
        monday_api_token=os.environ["MONDAY_API_TOKEN"],
        monday_board_id=os.environ["MONDAY_BOARD_ID"],
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        inbox_poll_interval_seconds=int(os.getenv("INBOX_POLL_INTERVAL_SECONDS", "120")),
        sent_check_poll_interval_seconds=int(
            os.getenv("SENT_CHECK_POLL_INTERVAL_SECONDS", "300")
        ),
        confidence_escalation_threshold=threshold,
    )
