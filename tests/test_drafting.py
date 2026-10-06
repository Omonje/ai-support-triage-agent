import pytest

from app.errors import GatewayError
from app.gateways.claude_gateway import ClaudeGateway
from app.gateways.knowledge_base_repo import Article
from app.service.drafting import build_draft


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


_ARTICLE = Article(
    id="defect_process",
    title="Defect and Damage Process",
    content="Start a defect claim within 14 days of delivery.",
)


def test_draft_reply_returns_the_claude_text():
    client = _FakeAnthropicClient(text="Thanks for reaching out, please start a defect claim...")
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    draft = gateway.draft_reply("Broken part", "It arrived cracked.", [_ARTICLE])

    assert "defect claim" in draft.text


def test_draft_reply_raises_gateway_error_when_api_call_fails():
    client = _FakeAnthropicClient(exc=RuntimeError("down"))
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [_ARTICLE])


def test_draft_reply_raises_gateway_error_on_empty_response():
    client = _FakeAnthropicClient(text="   ")
    gateway = ClaudeGateway(client, sleep=lambda s: None)

    with pytest.raises(GatewayError):
        gateway.draft_reply("subj", "body", [_ARTICLE])


class _FakeGatewayForDrafting:
    def __init__(self, text=None, exc=None):
        self._text = text
        self._exc = exc
        self.calls = []

    def draft_reply(self, subject, body, kb_articles):
        self.calls.append((subject, body, kb_articles))
        if self._exc:
            raise self._exc
        return type("DraftReply", (), {"text": self._text})()


def test_build_draft_refuses_to_run_with_no_kb_articles():
    gateway = _FakeGatewayForDrafting(text="should not be called")

    with pytest.raises(ValueError, match="no KB articles"):
        build_draft(gateway, "subj", "body", [])

    assert gateway.calls == []


def test_build_draft_passes_through_to_the_gateway():
    gateway = _FakeGatewayForDrafting(text="Here is your answer.")

    draft = build_draft(gateway, "subj", "body", [_ARTICLE])

    assert draft.text == "Here is your answer."
    assert gateway.calls == [("subj", "body", [_ARTICLE])]
