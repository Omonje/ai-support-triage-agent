from app.gateways.claude_gateway import RawClassification
from app.service.classification import Classification, classify


class _FakeGateway:
    def __init__(self, result):
        self._result = result

    def classify_message(self, subject, body):
        return self._result


def test_known_intent_and_urgency_pass_through():
    fake = _FakeGateway(
        RawClassification(
            intent="defect_complaint",
            urgency="high",
            confidence=0.9,
            reasoning="customer reports a broken part",
        )
    )

    result = classify(fake, "Broken part", "The part arrived cracked.")

    assert result == Classification(
        intent="defect_complaint",
        urgency="high",
        confidence=0.9,
        reasoning="customer reports a broken part",
    )


def test_unknown_intent_falls_back_to_other():
    fake = _FakeGateway(
        RawClassification(
            intent="totally_unknown_thing", urgency="low", confidence=0.5, reasoning=""
        )
    )

    result = classify(fake, "subj", "body")

    assert result.intent == "other"


def test_unknown_urgency_falls_back_to_medium():
    fake = _FakeGateway(
        RawClassification(intent="order_status", urgency="critical", confidence=0.5, reasoning="")
    )

    result = classify(fake, "subj", "body")

    assert result.urgency == "medium"


def test_confidence_above_one_is_clamped_to_one():
    fake = _FakeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=1.4, reasoning="")
    )

    result = classify(fake, "subj", "body")

    assert result.confidence == 1.0


def test_confidence_below_zero_is_clamped_to_zero():
    fake = _FakeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=-0.2, reasoning="")
    )

    result = classify(fake, "subj", "body")

    assert result.confidence == 0.0
