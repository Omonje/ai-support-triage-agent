"""The only place that talks to the Claude API for classification. Knows
nothing about escalation rules or what counts as a known intent, that is
the service layer's job. See app/gateways/gemini_gateway.py for the
provider-swapped equivalent, both implement the same two-method interface."""

import json
import time

from app.errors import GatewayError
from app.gateways.knowledge_base_repo import Article
from app.gateways.llm_types import (
    CLASSIFICATION_PROMPT_TEMPLATE,
    DRAFT_PROMPT_TEMPLATE,
    DraftReply,
    RawClassification,
)
from app.gateways.retry import retry_with_backoff

# Re-exported so existing `from app.gateways.claude_gateway import RawClassification`
# style imports keep working unchanged.
__all__ = ["ClaudeGateway", "DraftReply", "RawClassification", "DEFAULT_MODEL"]

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class ClaudeGateway:
    def __init__(self, client, model: str = DEFAULT_MODEL, sleep=time.sleep):
        self._client = client
        self._model = model
        self._sleep = sleep

    def classify_message(self, subject: str, body: str) -> RawClassification:
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(subject=subject, body=body)

        try:
            response = retry_with_backoff(
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                ),
                sleep=self._sleep,
            )
        except Exception as exc:
            raise GatewayError("claude", f"Classification call failed: {exc}") from exc

        try:
            text = response.content[0].text
        except (IndexError, AttributeError) as exc:
            raise GatewayError(
                "claude", f"Classification response had no readable content: {exc}"
            ) from exc

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GatewayError(
                "claude", f"Could not parse classification response as JSON: {exc}"
            ) from exc

        try:
            return RawClassification(
                intent=data["intent"],
                urgency=data["urgency"],
                confidence=float(data["confidence"]),
                reasoning=data.get("reasoning", ""),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GatewayError(
                "claude", f"Classification response was missing a required field: {exc}"
            ) from exc

    def draft_reply(self, subject: str, body: str, kb_articles: list[Article]) -> DraftReply:
        context = "\n\n".join(f"### {a.title}\n{a.content}" for a in kb_articles)
        prompt = DRAFT_PROMPT_TEMPLATE.format(subject=subject, body=body, context=context)

        try:
            response = retry_with_backoff(
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                ),
                sleep=self._sleep,
            )
        except Exception as exc:
            raise GatewayError("claude", f"Draft generation call failed: {exc}") from exc

        try:
            text = response.content[0].text
        except (IndexError, AttributeError) as exc:
            raise GatewayError(
                "claude", f"Draft response had no readable content: {exc}"
            ) from exc

        if not text.strip():
            raise GatewayError("claude", "Draft response was empty")

        return DraftReply(text=text.strip())
