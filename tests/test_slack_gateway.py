import pytest

from app.errors import GatewayError
from app.gateways.slack_gateway import SlackGateway


class _FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


class _FakeHttpPost:
    def __init__(self, response=None, exc=None):
        self._response = response or _FakeResponse()
        self._exc = exc
        self.calls = []

    def __call__(self, url, json=None):
        self.calls.append({"url": url, "json": json})
        if self._exc:
            raise self._exc
        return self._response


def test_send_alert_posts_the_text_to_the_webhook():
    http_post = _FakeHttpPost()
    gateway = SlackGateway(webhook_url="https://hooks.slack.test/abc", http_post=http_post)

    gateway.send_alert("Escalation needed: broken part")

    assert len(http_post.calls) == 1
    assert http_post.calls[0]["url"] == "https://hooks.slack.test/abc"
    assert http_post.calls[0]["json"] == {"text": "Escalation needed: broken part"}


def test_send_alert_raises_gateway_error_on_non_200_status():
    http_post = _FakeHttpPost(response=_FakeResponse(status_code=400, text="invalid_payload"))
    gateway = SlackGateway(webhook_url="https://hooks.slack.test/abc", http_post=http_post)

    with pytest.raises(GatewayError):
        gateway.send_alert("test")


def test_send_alert_raises_gateway_error_on_request_failure():
    http_post = _FakeHttpPost(exc=RuntimeError("network down"))
    gateway = SlackGateway(webhook_url="https://hooks.slack.test/abc", http_post=http_post)

    with pytest.raises(GatewayError):
        gateway.send_alert("test")
