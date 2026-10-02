"""Config is read once at start and checked. A bad or missing value stops
the program immediately with a clear message, never fails silently later
mid-request."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.errors import ConfigError

_REQUIRED = ["ANTHROPIC_API_KEY", "MONDAY_API_TOKEN", "MONDAY_BOARD_ID"]


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    gmail_oauth_client_path: str
    gmail_token_cache_path: str
    gmail_label: str
    gmail_escalation_label: str
    monday_api_token: str
    monday_board_id: str
    inbox_poll_interval_seconds: int
    sent_check_poll_interval_seconds: int
    confidence_escalation_threshold: float


def load_settings(env_file: str | None = ".env") -> Settings:
    if env_file:
        load_dotenv(env_file)

    missing = [name for name in _REQUIRED if not os.getenv(name)]
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
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        gmail_oauth_client_path=os.getenv("GMAIL_OAUTH_CLIENT_PATH", "credentials.json"),
        gmail_token_cache_path=os.getenv("GMAIL_TOKEN_CACHE_PATH", "gmail_token.json"),
        gmail_label=os.getenv("GMAIL_LABEL", "Triage-Demo"),
        gmail_escalation_label=os.getenv("GMAIL_ESCALATION_LABEL", "Needs-Human"),
        monday_api_token=os.environ["MONDAY_API_TOKEN"],
        monday_board_id=os.environ["MONDAY_BOARD_ID"],
        inbox_poll_interval_seconds=int(os.getenv("INBOX_POLL_INTERVAL_SECONDS", "120")),
        sent_check_poll_interval_seconds=int(
            os.getenv("SENT_CHECK_POLL_INTERVAL_SECONDS", "300")
        ),
        confidence_escalation_threshold=threshold,
    )
