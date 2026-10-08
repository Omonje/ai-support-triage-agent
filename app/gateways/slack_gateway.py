"""The only place that talks to Slack. A thin incoming-webhook wrapper,
one method, post a plain text message. Alerting is one-way and
best-effort: the pipeline never lets a Slack failure undo work that
already succeeded (see pipeline.py), it only logs it."""

import requests

from app.errors import GatewayError


class SlackGateway:
    def __init__(self, webhook_url: str, http_post=requests.post):
        self._webhook_url = webhook_url
        self._http_post = http_post

    def send_alert(self, text: str) -> None:
        try:
            response = self._http_post(self._webhook_url, json={"text": text})
        except Exception as exc:
            raise GatewayError("slack", f"Sending alert failed: {exc}") from exc

        if response.status_code != 200:
            raise GatewayError(
                "slack", f"Slack webhook returned {response.status_code}: {response.text}"
            )
