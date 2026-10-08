import pytest

from app.errors import GatewayError
from app.gateways.groq_gateway import GroqGateway


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeCompletionResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content=None, exc=None):
        self._content = content
        self._exc = exc

    def create(self, model, messages):
        if self._exc:
            raise self._exc
        return _FakeCompletionResponse(self._content)


class _FakeChat:
    def __init__(self, content=None, exc=None):
        self.completions = _FakeCompletions(content=content, exc=exc)


class _FakeGroqClient:
    def __init__(self, content=None, exc=None):
        self.chat = _FakeChat(content=content, exc=exc)


def test_classify_parses_plain_json_response():
    client = _FakeGroqClient(
        content='{"intent": "order_status", "urgency": "low", '
        '"confidence": 0.8, "reasoning": "asking where order is"}'
    )
    gateway = GroqGateway(client, sleep=lambda s: None)

    result = gateway.classify_message("Where's my order", "Hi, I ordered 2 weeks ago.")

    assert result.intent == "order_status"
    assert result.confidence == 0.8


def test_classify_strips_markdown_code_fences():
    client = _FakeGroqClient(
        content='```json\n{"intent": "quote_request", "urgency": "low", '
        '"confidence": 0.7, "reasoning": "asking for a quote"}\n```'
    )
    gateway = GroqGateway(client, sleep=lambda s: None)

    result = gateway.classify_message("subj", "body")

    assert result.intent == "quote_request"


def test_classify_raises_gateway_error_on_malformed_json():
    client = _FakeGroqClient(content="not json at all")
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_when_api_call_fails():
    client = _FakeGroqClient(exc=RuntimeError("down"))
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_on_missing_fields():
    client = _FakeGroqClient(content='{"intent": "order_status"}')
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_classify_raises_gateway_error_on_empty_response():
    client = _FakeGroqClient(content=None)
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.classify_message("subj", "body")


def test_draft_reply_returns_the_text():
    client = _FakeGroqClient(content="Thanks for reaching out, start a defect claim...")
    gateway = GroqGateway(client, sleep=lambda s: None)

    draft = gateway.draft_reply("Broken part", "It arrived cracked.", [])

    assert "defect claim" in draft.text


def test_draft_reply_raises_gateway_error_on_empty_response():
    client = _FakeGroqClient(content="   ")
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [])


def test_draft_reply_raises_gateway_error_on_api_failure():
    client = _FakeGroqClient(exc=RuntimeError("down"))
    gateway = GroqGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [])
