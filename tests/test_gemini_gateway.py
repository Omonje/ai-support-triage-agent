import pytest

from app.errors import GatewayError
from app.gateways.gemini_gateway import GeminiGateway


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, text=None, exc=None):
        self._text = text
        self._exc = exc

    def generate_content(self, model, contents, config=None):
        if self._exc:
            raise self._exc
        return _FakeResponse(self._text)


class _FakeGenaiClient:
    def __init__(self, text=None, exc=None):
        self.models = _FakeModels(text=text, exc=exc)


def test_classify_parses_plain_json_response():
    client = _FakeGenaiClient(
        text='{"intent": "order_status", "urgency": "low", '
        '"confidence": 0.8, "reasoning": "asking where order is"}'
    )
    gateway = GeminiGateway(client)

    result = gateway.classify_message("Where's my order", "Hi, I ordered 2 weeks ago.")

    assert result.intent == "order_status"
    assert result.confidence == 0.8


def test_classify_strips_markdown_code_fences():
    client = _FakeGenaiClient(
        text='```json\n{"intent": "quote_request", "urgency": "low", '
        '"confidence": 0.7, "reasoning": "asking for a quote"}\n```'
    )
    gateway = GeminiGateway(client)

    result = gateway.classify_message("subj", "body")

    assert result.intent == "quote_request"


def test_classify_raises_gateway_error_on_malformed_json():
    client = _FakeGenaiClient(text="not json at all")
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_when_api_call_fails():
    client = _FakeGenaiClient(exc=RuntimeError("down"))
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_on_missing_fields():
    client = _FakeGenaiClient(text='{"intent": "order_status"}')
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_on_empty_response():
    client = _FakeGenaiClient(text=None)
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_draft_reply_returns_the_text():
    client = _FakeGenaiClient(text="Thanks for reaching out, start a defect claim...")
    gateway = GeminiGateway(client)

    draft = gateway.draft_reply("Broken part", "It arrived cracked.", [])

    assert "defect claim" in draft.text


def test_draft_reply_raises_gateway_error_on_empty_response():
    client = _FakeGenaiClient(text="   ")
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [])


def test_draft_reply_raises_gateway_error_on_api_failure():
    client = _FakeGenaiClient(exc=RuntimeError("down"))
    gateway = GeminiGateway(client)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [])
