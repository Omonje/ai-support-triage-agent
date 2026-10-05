"""Seeds the dedicated Gmail account with synthetic manufacturer support
messages, labeled Triage-Demo so the agent picks them up. Every message is
fabricated for this project, no real customer or company involved.

Safe to re-run: each run inserts a fresh batch, it does not check for or
remove previous runs' messages.

Usage: python -m scripts.seed_test_messages
"""

from app.config import load_settings
from app.gateways.gmail_auth import build_gmail_service
from app.gateways.gmail_gateway import GmailGateway

_TO_ADDRESS = "support@manufacturer-demo.test"

_MESSAGES = [
    # (sender, subject, body) - covers all 5 intents, varied urgency,
    # a few deliberately ambiguous ones to exercise the confidence threshold.
    (
        "j.ramirez@buyer-example.test",
        "Order status check",
        "Hi, just checking on the status of order #4521, placed last week. No rush, just curious.",
    ),
    (
        "procurement@fabco-example.test",
        "No tracking update in 4 days",
        "My order was supposed to arrive yesterday and I haven't gotten a tracking update in 4 days. Can you check?",
    ),
    (
        "ops@steelworks-example.test",
        "Cracked bracket, missing bolt hole",
        "The bracket I received is cracked and missing a bolt hole entirely. This is unacceptable for a structural part, "
        "please advise on replacement.",
    ),
    (
        "qc@partsdepot-example.test",
        "Multiple units with surface defects",
        "Opened the box and three of the ten units have visible surface defects. Photos attached in a follow-up.",
    ),
    (
        "buyer1@connectorsinc-example.test",
        "Quote for model-B connector",
        "Can I get a quote for 200 units of the model-B connector in aluminum? No deadline on our end.",
    ),
    (
        "d.chen@rushorders-example.test",
        "Rush quote needed, 3 week deadline",
        "Need a rush quote for 5000 units, deadline is in 3 weeks, can you turn this around fast? Let me know what you need from us.",
    ),
    (
        "logistics@midwest-example.test",
        "Tracking stuck for 5 days",
        "Tracking hasn't updated in 5 days and the order was supposed to ship over a week ago. Starting to get worried.",
    ),
    (
        "k.patel@deadline-example.test",
        "URGENT: shipment 2 weeks late",
        "This shipment is now 2 weeks late and we have a client deadline tomorrow. Need an update immediately, this is urgent.",
    ),
    (
        "visitor@curious-example.test",
        "Showroom visit",
        "Do you have a showroom I can visit in person? Would love to see the parts before ordering.",
    ),
    (
        "compliance@bigcorp-example.test",
        "ISO certification question",
        "What's your company's ISO certification status? Need this for our vendor approval process.",
    ),
    (
        "a.wong@smallbiz-example.test",
        "Has order #7788 shipped?",
        "Wondering if order #7788 has shipped yet. Thanks!",
    ),
    (
        "qc2@tolerance-example.test",
        "Slight color variation, within tolerance?",
        "One of the parts arrived with a slightly off color, is this within tolerance or should I be concerned?",
    ),
    (
        "buyer2@stainless-example.test",
        "Custom stainless bracket quote",
        "What's the lead time and price for a custom bracket in stainless steel, qty 50?",
    ),
    (
        "t.osei@tracking-example.test",
        "Tracking says label created, no movement",
        "Just curious why tracking says 'label created' but no movement for 2 days. Is that normal?",
    ),
    (
        "m.silva@cancel-example.test",
        "Need to cancel order #3321",
        "I'd like to cancel order #3321 if it hasn't shipped yet. Please confirm either way.",
    ),
    (
        "safety@concerned-example.test",
        "Cracked housing, sharp edge exposed",
        "The housing on this unit cracked after one day of use and there's a sharp edge exposed. Worried about injury, "
        "please advise urgently.",
    ),
    (
        "r.kim@rushshipping-example.test",
        "Confirm rush shipping on order #9012",
        "Can you confirm if order #9012 includes the rush shipping I paid for? Want to make sure before it ships.",
    ),
    (
        "sample@trial-example.test",
        "Sample kits available?",
        "Do you offer sample kits before placing a bulk order? Would like to test fit before committing to a large run.",
    ),
]


def main() -> None:
    settings = load_settings()
    service = build_gmail_service(settings.gmail_oauth_client_path, settings.gmail_token_cache_path)
    gateway = GmailGateway(
        service,
        label=settings.gmail_label,
        processed_label=settings.gmail_processed_label,
        escalation_label=settings.gmail_escalation_label,
    )

    for sender, subject, body in _MESSAGES:
        message_id = gateway.insert_message(
            sender=sender,
            to=_TO_ADDRESS,
            subject=subject,
            body_text=body,
            label_names=[settings.gmail_label],
        )
        print(f"Inserted {message_id}: {subject!r} from {sender}")

    print(f"\nDone. Inserted {len(_MESSAGES)} synthetic messages under '{settings.gmail_label}'.")


if __name__ == "__main__":
    main()
