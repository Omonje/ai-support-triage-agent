"""The only place that talks to the Claude API for classification. Knows
nothing about escalation rules or what counts as a known intent, that is
the service layer's job."""

import json
from dataclasses import dataclass

from app.errors import GatewayError

CLASSIFICATION_MODEL = "claude-sonnet-4-5-20250929"

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


@dataclass(frozen=True)
class RawClassification:
    intent: str
    urgency: str
    confidence: float
    reasoning: str


class ClaudeGateway:
    def __init__(self, client, model: str = CLASSIFICATION_MODEL):
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
