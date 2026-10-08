"""Runs the full triage pipeline once against every new message under the
Triage-Demo label: classify, escalate-or-draft, write a monday.com item,
mark the message processed. Safe to re-run, already-processed messages
(Gmail's Processed label) are skipped automatically.

Usage: python -m scripts.run_pipeline
"""

from app.config import load_settings
from app.errors import ConfigError
from app.gateways.gmail_auth import build_gmail_service
from app.gateways.gmail_gateway import GmailGateway
from app.gateways.knowledge_base_repo import load_articles
from app.gateways.monday_gateway import MondayGateway
from app.gateways.slack_gateway import SlackGateway
from app.service.pipeline import process_new_messages


def _build_llm_gateway(settings):
    if settings.llm_provider == "claude":
        from anthropic import Anthropic

        from app.gateways.claude_gateway import ClaudeGateway

        return ClaudeGateway(Anthropic(api_key=settings.anthropic_api_key))

    if settings.llm_provider == "gemini":
        import os

        from google import genai

        from app.gateways.gemini_gateway import GeminiGateway

        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        return GeminiGateway(genai.Client(api_key=settings.google_api_key), model=model)

    if settings.llm_provider == "groq":
        import os

        from groq import Groq

        from app.gateways.groq_gateway import GroqGateway

        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        return GroqGateway(Groq(api_key=settings.groq_api_key), model=model)

    raise ConfigError(f"No gateway wired up for LLM_PROVIDER={settings.llm_provider!r}")


def main() -> None:
    settings = load_settings()

    llm_gateway = _build_llm_gateway(settings)
    print(f"Using LLM provider: {settings.llm_provider}")

    gmail_service = build_gmail_service(settings.gmail_oauth_client_path, settings.gmail_token_cache_path)
    gmail_gateway = GmailGateway(
        gmail_service,
        label=settings.gmail_label,
        processed_label=settings.gmail_processed_label,
        escalation_label=settings.gmail_escalation_label,
    )

    monday_gateway = MondayGateway(api_token=settings.monday_api_token, board_id=settings.monday_board_id)
    kb_articles = load_articles()

    slack_gateway = SlackGateway(webhook_url=settings.slack_webhook_url) if settings.slack_webhook_url else None
    if slack_gateway is None:
        print("SLACK_WEBHOOK_URL not set, running without Slack alerts.")

    results, failures = process_new_messages(
        gmail_gateway=gmail_gateway,
        llm_gateway=llm_gateway,
        monday_gateway=monday_gateway,
        kb_articles=kb_articles,
        confidence_threshold=settings.confidence_escalation_threshold,
        slack_gateway=slack_gateway,
    )

    print(f"Processed {len(results)} message(s), {len(failures)} failure(s).")
    for result in results:
        marker = "ESCALATED" if result.escalated else "DRAFTED "
        print(f"  [{marker}] {result.gmail_message_id} -> monday item {result.monday_item_id} ({result.status})")
    for failure in failures:
        print(f"  [FAILED  ] {failure.gmail_message_id}: {failure.error}")
    if failures:
        print("\nFailed messages were NOT marked processed, re-run this script to retry them.")


if __name__ == "__main__":
    main()
