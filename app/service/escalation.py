"""The two escalation triggers agreed in the plan: a sensitive intent, or
confidence below the configured threshold. Either one sends the message
to a human instead of drafting a reply. Knows nothing about Gmail or
monday.com, only the classification and the threshold."""

from dataclasses import dataclass

from app.service.classification import Classification

# Defect complaints can involve product safety or liability, always route
# to a human rather than let the agent judge severity on its own.
SENSITIVE_INTENTS = {"defect_complaint"}


@dataclass(frozen=True)
class EscalationDecision:
    escalate: bool
    reason: str | None


def decide_escalation(classification: Classification, confidence_threshold: float) -> EscalationDecision:
    if classification.intent in SENSITIVE_INTENTS:
        return EscalationDecision(
            escalate=True, reason=f"sensitive intent: {classification.intent}"
        )

    if classification.confidence < confidence_threshold:
        return EscalationDecision(
            escalate=True,
            reason=(
                f"low confidence: {classification.confidence:.2f} "
                f"< {confidence_threshold:.2f}"
            ),
        )

    return EscalationDecision(escalate=False, reason=None)
