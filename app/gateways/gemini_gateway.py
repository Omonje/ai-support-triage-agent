"""The Gemini-backed equivalent of ClaudeGateway, same two-method
interface (classify_message, draft_reply), same shared prompts and
return types, so the service layer and the pipeline don't know or care
which provider answered. Swapped in when ANTHROPIC credits aren't
available; see DECISIONS.md."""

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

DEFAULT_MODEL = "gemini-flash-latest"


class GeminiGateway:
    def __init__(self, client, model: str = DEFAULT_MODEL, sleep=time.sleep):
        self._client = client
        self._model = model
        self._sleep = sleep

    def classify_message(self, subject: str, body: str) -> RawClassification:
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(subject=subject, body=body)

        try:
            response = retry_with_backoff(
                lambda: self._client.models.generate_content(model=self._model, contents=prompt),
                sleep=self._sleep,
            )
        except Exception as exc:
            raise GatewayError("gemini", f"Classification call failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise GatewayError("gemini", "Classification response had no readable content")

        try:
            data = json.loads(_strip_markdown_fences(text))
        except json.JSONDecodeError as exc:
            raise GatewayError(
                "gemini", f"Could not parse classification response as JSON: {exc}"
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
                "gemini", f"Classification response was missing a required field: {exc}"
            ) from exc

    def draft_reply(self, subject: str, body: str, kb_articles: list[Article]) -> DraftReply:
        context = "\n\n".join(f"### {a.title}\n{a.content}" for a in kb_articles)
        prompt = DRAFT_PROMPT_TEMPLATE.format(subject=subject, body=body, context=context)

        try:
            response = retry_with_backoff(
                lambda: self._client.models.generate_content(model=self._model, contents=prompt),
                sleep=self._sleep,
            )
        except Exception as exc:
            raise GatewayError("gemini", f"Draft generation call failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise GatewayError("gemini", "Draft response was empty")

        return DraftReply(text=text.strip())


def _strip_markdown_fences(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json ... ``` despite being asked
    not to. Strip it defensively rather than fail on a cosmetic wrapper."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped
