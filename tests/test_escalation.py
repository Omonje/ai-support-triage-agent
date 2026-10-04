from app.service.classification import Classification
from app.service.escalation import decide_escalation


def _classification(intent="order_status", urgency="low", confidence=0.9):
    return Classification(intent=intent, urgency=urgency, confidence=confidence, reasoning="")


def test_sensitive_intent_escalates_even_with_high_confidence():
    decision = decide_escalation(_classification(intent="defect_complaint", confidence=0.95), 0.6)

    assert decision.escalate is True
    assert "sensitive" in decision.reason
    assert "defect_complaint" in decision.reason


def test_low_confidence_escalates_even_with_non_sensitive_intent():
    decision = decide_escalation(_classification(intent="order_status", confidence=0.3), 0.6)

    assert decision.escalate is True
    assert "confidence" in decision.reason


def test_non_sensitive_high_confidence_does_not_escalate():
    decision = decide_escalation(_classification(intent="order_status", confidence=0.9), 0.6)

    assert decision.escalate is False
    assert decision.reason is None


def test_confidence_exactly_at_threshold_does_not_escalate():
    decision = decide_escalation(_classification(intent="order_status", confidence=0.6), 0.6)

    assert decision.escalate is False


def test_confidence_just_below_threshold_escalates():
    decision = decide_escalation(_classification(intent="order_status", confidence=0.59), 0.6)

    assert decision.escalate is True
