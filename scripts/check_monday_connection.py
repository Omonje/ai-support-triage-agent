"""Run this to confirm real connectivity to the monday.com board: creates
one test item, updates its status, and prints both results. No browser
interaction needed, just the API token already in .env.

Usage: python -m scripts.check_monday_connection
"""

from datetime import date

from app.config import load_settings
from app.gateways.monday_gateway import MondayGateway, TriageRecord


def main() -> None:
    settings = load_settings()
    gateway = MondayGateway(api_token=settings.monday_api_token, board_id=settings.monday_board_id)

    record = TriageRecord(
        gmail_message_id="connectivity_check",
        item_name="Connectivity check item (safe to delete)",
        status="Classified",
        intent="order_status",
        urgency="low",
        confidence=0.5,
        kb_articles_used="none",
        reasoning="this item was created by scripts/check_monday_connection.py",
        processed_at=date.today().isoformat(),
    )

    item_id = gateway.create_item(record)
    print(f"Created item {item_id}.")

    gateway.update_item_status(item_id, "Sent")
    print(f"Updated item {item_id} status to 'Sent'. Check the board to confirm, then delete this test item.")


if __name__ == "__main__":
    main()
