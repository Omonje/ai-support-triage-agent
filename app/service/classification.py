"""The rules for turning a raw Claude classification into one we trust
enough to act on. Knows nothing about Gmail, monday.com, or HTTP."""

from dataclasses import dataclass

KNOWN_INTENTS = {"order_status", "defect_complaint", "quote_request", "shipping_delay", "other"}
KNOWN_URGENCY = {"low", "medium", "high"}


@dataclass(frozen=True)
class Classification:
    intent: str
    urgency: str
    confidence: float
    reasoning: str


def classify(gateway, subject: str, body: str) -> Classification:
    raw = gateway.classify_message(subject, body)

    intent = raw.intent if raw.intent in KNOWN_INTENTS else "other"
    urgency = raw.urgency if raw.urgency in KNOWN_URGENCY else "medium"
    confidence = min(1.0, max(0.0, raw.confidence))

    return Classification(intent=intent, urgency=urgency, confidence=confidence, reasoning=raw.reasoning)
