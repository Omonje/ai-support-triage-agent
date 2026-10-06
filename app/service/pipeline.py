"""Ties classification, escalation, retrieval, and drafting together into
the per-message flow: one new Gmail message in, one monday.com item out,
the message marked processed either way. This is the rule for how a
message moves through the system end to end."""

from dataclasses import dataclass
from datetime import date

from app.gateways.monday_gateway import TriageRecord
from app.service.classification import classify
from app.service.drafting import build_draft
from app.service.escalation import decide_escalation
from app.service.retrieval import retrieve

STATUS_DRAFT_READY = "Draft Ready for Approval"
STATUS_ESCALATED = "Escalated - Needs Human"


@dataclass(frozen=True)
class ProcessingResult:
    gmail_message_id: str
    monday_item_id: str
    escalated: bool
    status: str


@dataclass(frozen=True)
class ProcessingFailure:
    gmail_message_id: str
    error: str


def process_one_message(
    message,
    *,
    llm_gateway,
    gmail_gateway,
    monday_gateway,
    kb_articles,
    confidence_threshold: float,
) -> ProcessingResult:
    classification = classify(llm_gateway, message.subject, message.body)
    decision = decide_escalation(classification, confidence_threshold)

    if decision.escalate:
        gmail_gateway.apply_label(message.id, gmail_gateway.escalation_label)
        status = STATUS_ESCALATED
        gmail_draft_id = ""
        kb_articles_used = ""
        reasoning = decision.reason
    else:
        retrieved = retrieve(message.body, kb_articles, top_k=2)
        draft = build_draft(llm_gateway, message.subject, message.body, retrieved)
        gmail_draft_id = gmail_gateway.create_draft(
            message.thread_id, message.sender, message.subject, draft.text
        )
        status = STATUS_DRAFT_READY
        kb_articles_used = ", ".join(article.id for article in retrieved)
        reasoning = classification.reasoning

    record = TriageRecord(
        gmail_message_id=message.id,
        item_name=f"{message.subject} - {message.sender}",
        status=status,
        intent=classification.intent,
        urgency=classification.urgency,
        confidence=classification.confidence,
        kb_articles_used=kb_articles_used,
        reasoning=reasoning,
        processed_at=date.today().isoformat(),
        gmail_draft_id=gmail_draft_id,
    )
    monday_item_id = monday_gateway.create_item(record)

    gmail_gateway.mark_processed(message.id)

    return ProcessingResult(
        gmail_message_id=message.id,
        monday_item_id=monday_item_id,
        escalated=decision.escalate,
        status=status,
    )


def process_new_messages(
    *, gmail_gateway, llm_gateway, monday_gateway, kb_articles, confidence_threshold: float
) -> tuple[list[ProcessingResult], list[ProcessingFailure]]:
    """One message failing (a transient API error, most often) does not
    stop the rest of the batch. A failed message is never marked
    processed, so it's picked up again on the next run rather than
    silently dropped."""
    results = []
    failures = []
    for message_id in gmail_gateway.list_new_message_ids():
        try:
            message = gmail_gateway.get_message(message_id)
            result = process_one_message(
                message,
                llm_gateway=llm_gateway,
                gmail_gateway=gmail_gateway,
                monday_gateway=monday_gateway,
                kb_articles=kb_articles,
                confidence_threshold=confidence_threshold,
            )
            results.append(result)
        except Exception as exc:
            failures.append(ProcessingFailure(gmail_message_id=message_id, error=str(exc)))
    return results, failures
