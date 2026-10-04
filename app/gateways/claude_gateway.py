"""The only place that talks to the Claude API for classification. Knows
nothing about escalation rules or what counts as a known intent, that is
the service layer's job."""

import json
from dataclasses import dataclass

from app.errors import GatewayError
from app.gateways.knowledge_base_repo import Article

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

_PROMPT_TEMPLATE = """You triage support emails for a manufacturer. Read \
the message and classify it. Reply with ONLY a JSON object, no other text, \
in this exact shape:

{{"intent": "<one of: order_status, defect_complaint, quote_request, \
shipping_delay, other>", "urgency": "<one of: low, medium, high>", \
"confidence": <number between 0 and 1, how confident you are in this \
classification>, "reasoning": "<one short sentence>"}}

Subject: {subject}

Body:
{body}
"""

_DRAFT_PROMPT_TEMPLATE = """You draft support replies for a manufacturer. \
Write a short, professional reply to the customer's message below, using \
ONLY the policy information provided. Do not invent any policy detail, \
price, date, or timeframe that is not in the provided articles. If the \
articles do not fully answer the question, say plainly that a team \
member will follow up with specifics, do not guess. Sign off as "the \
support team," never invent a person's name.

Policy articles:
{context}

Customer's subject: {subject}

Customer's message:
{body}

Reply:
"""


@dataclass(frozen=True)
class DraftReply:
    text: str


@dataclass(frozen=True)
class RawClassification:
    intent: str
    urgency: str
    confidence: float
    reasoning: str


class ClaudeGateway:
    def __init__(self, client, model: str = DEFAULT_MODEL):
        self._client = client
        self._model = model

    def classify_message(self, subject: str, body: str) -> RawClassification:
        prompt = _PROMPT_TEMPLATE.format(subject=subject, body=body)

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
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
        prompt = _DRAFT_PROMPT_TEMPLATE.format(subject=subject, body=body, context=context)

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
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
