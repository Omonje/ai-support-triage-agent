"""Closes the loop: for every monday.com item still in "Draft Ready for
Approval", check whether its Gmail draft has been sent or removed, and
flip the item to "Sent" if so. No LLM calls, safe to run anytime.

Usage: python -m scripts.check_sent_drafts
"""

from app.config import load_settings
from app.gateways.gmail_auth import build_gmail_service
from app.gateways.gmail_gateway import GmailGateway
from app.gateways.monday_gateway import MondayGateway
from app.service.pipeline import STATUS_DRAFT_READY
from app.service.sent_detection import check_sent_drafts

SENT_STATUS = "Sent"


def main() -> None:
    settings = load_settings()

    gmail_service = build_gmail_service(settings.gmail_oauth_client_path, settings.gmail_token_cache_path)
    gmail_gateway = GmailGateway(
        gmail_service,
        label=settings.gmail_label,
        processed_label=settings.gmail_processed_label,
        escalation_label=settings.gmail_escalation_label,
    )
    monday_gateway = MondayGateway(api_token=settings.monday_api_token, board_id=settings.monday_board_id)

    results = check_sent_drafts(gmail_gateway, monday_gateway, STATUS_DRAFT_READY, SENT_STATUS)

    print(f"Checked {len(results)} pending draft(s).")
    for result in results:
        state = "SENT (updated)" if result.sent else "still pending"
        print(f"  {result.monday_item_id} (draft {result.gmail_draft_id}): {state}")


if __name__ == "__main__":
    main()
