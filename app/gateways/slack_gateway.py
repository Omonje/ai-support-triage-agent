"""The only place that talks to Slack. A thin incoming-webhook wrapper,
one method, post a plain text message. Alerting is one-way and
best-effort: nothing that calls send_alert_best_effort ever lets a
Slack failure undo work (a draft, an escalation label, a monday.com
item, a successful pipeline startup) that already succeeded."""

import requests

from app.errors import GatewayError
from app.logging_setup import get_logger

logger = get_logger(__name__)


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


def send_alert_best_effort(slack_gateway, text: str) -> None:
    """Logged, not raised: a Slack outage must never fail or mask the
    real work that triggered the alert in the first place."""
    try:
        slack_gateway.send_alert(text)
    except Exception as exc:
        logger.warning("Slack alert failed to send: %s", exc)
