"""Run this once to complete the Gmail OAuth consent and confirm real
connectivity. The first run opens a browser window asking you to log in
and approve access; after that, a cached token is reused automatically.

Usage: python -m scripts.check_gmail_connection
"""

from app.config import load_settings
from app.gateways.gmail_auth import build_gmail_service
from app.gateways.gmail_gateway import GmailGateway


def main() -> None:
    settings = load_settings()
    service = build_gmail_service(settings.gmail_oauth_client_path, settings.gmail_token_cache_path)
    gateway = GmailGateway(
        service,
        label=settings.gmail_label,
        processed_label=settings.gmail_processed_label,
        escalation_label=settings.gmail_escalation_label,
    )

    message_ids = gateway.list_new_message_ids()
    print(f"Connected. Found {len(message_ids)} unprocessed message(s) under '{settings.gmail_label}'.")

    for message_id in message_ids[:5]:
        message = gateway.get_message(message_id)
        print(f"  - {message.subject!r} from {message.sender}")


if __name__ == "__main__":
    main()
