from app.service.sent_detection import check_sent_drafts

PENDING_STATUS = "Draft Ready for Approval"
SENT_STATUS = "Sent"


class _FakeGmailGateway:
    def __init__(self, existing_draft_ids: set):
        self._existing = existing_draft_ids
        self.checked = []

    def draft_exists(self, draft_id):
        self.checked.append(draft_id)
        return draft_id in self._existing


class _FakeMondayGateway:
    def __init__(self, pending_items):
        self._pending_items = pending_items
        self.status_updates = []

    def list_items_with_status(self, status):
        assert status == PENDING_STATUS
        return self._pending_items

    def update_item_status(self, item_id, status):
        self.status_updates.append((item_id, status))


def test_draft_still_pending_is_not_marked_sent():
    gmail = _FakeGmailGateway(existing_draft_ids={"draft_1"})
    monday = _FakeMondayGateway([{"item_id": "item_1", "gmail_draft_id": "draft_1"}])

    results = check_sent_drafts(gmail, monday, PENDING_STATUS, SENT_STATUS)

    assert results[0].sent is False
    assert monday.status_updates == []


def test_draft_no_longer_there_is_marked_sent():
    gmail = _FakeGmailGateway(existing_draft_ids=set())
    monday = _FakeMondayGateway([{"item_id": "item_1", "gmail_draft_id": "draft_1"}])

    results = check_sent_drafts(gmail, monday, PENDING_STATUS, SENT_STATUS)

    assert results[0].sent is True
    assert monday.status_updates == [("item_1", "Sent")]


def test_checks_every_pending_item_independently():
    gmail = _FakeGmailGateway(existing_draft_ids={"draft_1"})
    monday = _FakeMondayGateway(
        [
            {"item_id": "item_1", "gmail_draft_id": "draft_1"},
            {"item_id": "item_2", "gmail_draft_id": "draft_2"},
        ]
    )

    results = check_sent_drafts(gmail, monday, PENDING_STATUS, SENT_STATUS)

    assert len(results) == 2
    assert monday.status_updates == [("item_2", "Sent")]


def test_items_with_no_draft_id_are_skipped():
    gmail = _FakeGmailGateway(existing_draft_ids=set())
    monday = _FakeMondayGateway([{"item_id": "item_1", "gmail_draft_id": ""}])

    results = check_sent_drafts(gmail, monday, PENDING_STATUS, SENT_STATUS)

    assert results == []
    assert gmail.checked == []
