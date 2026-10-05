"""Runs the full triage pipeline once against every new message under the
Triage-Demo label: classify, escalate-or-draft, write a monday.com item,
mark the message processed. Safe to re-run, already-processed messages
(Gmail's Processed label) are skipped automatically.

Usage: python -m scripts.run_pipeline
"""

from anthropic import Anthropic

from app.config import load_settings
from app.gateways.claude_gateway import ClaudeGateway
from app.gateways.gmail_auth import build_gmail_service
from app.gateways.gmail_gateway import GmailGateway
from app.gateways.knowledge_base_repo import load_articles
from app.gateways.monday_gateway import MondayGateway
from app.service.pipeline import process_new_messages


def main() -> None:
    settings = load_settings()

    claude_gateway = ClaudeGateway(Anthropic(api_key=settings.anthropic_api_key))

    gmail_service = build_gmail_service(settings.gmail_oauth_client_path, settings.gmail_token_cache_path)
    gmail_gateway = GmailGateway(
        gmail_service,
        label=settings.gmail_label,
        processed_label=settings.gmail_processed_label,
        escalation_label=settings.gmail_escalation_label,
    )

    monday_gateway = MondayGateway(api_token=settings.monday_api_token, board_id=settings.monday_board_id)
    kb_articles = load_articles()

    results = process_new_messages(
        gmail_gateway=gmail_gateway,
        claude_gateway=claude_gateway,
        monday_gateway=monday_gateway,
        kb_articles=kb_articles,
        confidence_threshold=settings.confidence_escalation_threshold,
    )

    print(f"Processed {len(results)} message(s).")
    for result in results:
        marker = "ESCALATED" if result.escalated else "DRAFTED "
        print(f"  [{marker}] {result.gmail_message_id} -> monday item {result.monday_item_id} ({result.status})")


if __name__ == "__main__":
    main()
