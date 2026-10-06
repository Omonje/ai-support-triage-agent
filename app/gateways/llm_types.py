"""Provider-neutral types and prompts shared by every LLM gateway
(Claude, Gemini, or any future provider). The prompt text itself doesn't
depend on which model answers it, only the transport (how the call is
made and the response unwrapped) differs per gateway."""

from dataclasses import dataclass

CLASSIFICATION_PROMPT_TEMPLATE = """You triage support emails for a manufacturer. Read \
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

DRAFT_PROMPT_TEMPLATE = """You draft support replies for a manufacturer. \
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
class RawClassification:
    intent: str
    urgency: str
    confidence: float
    reasoning: str


@dataclass(frozen=True)
class DraftReply:
    text: str
