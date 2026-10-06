"""Closes the loop without a webhook: for every monday.com item still
sitting in the pending-approval status, check whether its Gmail draft has
been sent or removed, and if so, flip the item to the sent status."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SentCheckResult:
    monday_item_id: str
    gmail_draft_id: str
    sent: bool


def check_sent_drafts(
    gmail_gateway, monday_gateway, pending_status: str, sent_status: str
) -> list[SentCheckResult]:
    results = []
    for item in monday_gateway.list_items_with_status(pending_status):
        draft_id = item["gmail_draft_id"]
        if not draft_id:
            continue

        still_pending = gmail_gateway.draft_exists(draft_id)
        if not still_pending:
            monday_gateway.update_item_status(item["item_id"], sent_status)

        results.append(
            SentCheckResult(
                monday_item_id=item["item_id"], gmail_draft_id=draft_id, sent=not still_pending
            )
        )
    return results
