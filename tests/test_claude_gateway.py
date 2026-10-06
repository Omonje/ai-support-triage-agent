import pytest

from app.errors import GatewayError
from app.gateways.claude_gateway import ClaudeGateway


class _FakeContentBlock:
    def __init__(self, text):
        self.text = text


class _FakeResponse:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class _FakeMessages:
    def __init__(self, text=None, exc=None):
        self._text = text
        self._exc = exc

    def create(self, **kwargs):
        if self._exc:
            raise self._exc
        return _FakeResponse(self._text)


class _FakeAnthropicClient:
    def __init__(self, text=None, exc=None):
        self.messages = _FakeMessages(text=text, exc=exc)


def test_parses_valid_json_response():
    client = _FakeAnthropicClient(
        text='{"intent": "order_status", "urgency": "low", '
        '"confidence": 0.8, "reasoning": "asking where order is"}'
    )
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    result = gateway.classify_message("Where's my order", "Hi, I ordered 2 weeks ago.")

    assert result.intent == "order_status"
    assert result.urgency == "low"
    assert result.confidence == 0.8
    assert result.reasoning == "asking where order is"


def test_raises_gateway_error_on_malformed_json():
    client = _FakeAnthropicClient(text="not json at all")
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_raises_gateway_error_when_api_call_fails():
    client = _FakeAnthropicClient(exc=RuntimeError("network down"))
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_raises_gateway_error_on_missing_fields():
    client = _FakeAnthropicClient(text='{"intent": "order_status"}')
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")
