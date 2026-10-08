from app.gateways.claude_gateway import DraftReply, RawClassification
from app.gateways.gmail_gateway import EmailMessage
from app.gateways.knowledge_base_repo import Article
from app.service.pipeline import process_new_messages


class _FakeClaudeGateway:
    def __init__(
        self,
        classification: RawClassification,
        draft_text: str = "Thanks, here is your answer.",
        fail_for_message_ids: set | None = None,
    ):
        self._classification = classification
        self._draft_text = draft_text
        self._fail_for = fail_for_message_ids or set()
        self.classify_calls = []
        self.draft_calls = []

    def classify_message(self, subject, body):
        self.classify_calls.append((subject, body))
        if subject in self._fail_for:
            raise RuntimeError(f"simulated transient failure classifying {subject!r}")
        return self._classification

    def draft_reply(self, subject, body, kb_articles):
        self.draft_calls.append((subject, body, kb_articles))
        return DraftReply(text=self._draft_text)


class _FakeGmailGateway:
    def __init__(self, messages: dict):
        self._messages = messages
        self.escalation_label = "Needs-Human"
        self.applied_labels = []
        self.created_drafts = []
        self.marked_processed = []

    def list_new_message_ids(self):
        return list(self._messages.keys())

    def get_message(self, message_id):
        return self._messages[message_id]

    def apply_label(self, message_id, label_name):
        self.applied_labels.append((message_id, label_name))

    def create_draft(self, thread_id, to, subject, body_text):
        self.created_drafts.append((thread_id, to, subject, body_text))
        return "draft_1"

    def mark_processed(self, message_id):
        self.marked_processed.append(message_id)


class _FakeMondayGateway:
    def __init__(self):
        self.created_records = []

    def create_item(self, record):
        self.created_records.append(record)
        return f"item_for_{record.gmail_message_id}"


class _FakeSlackGateway:
    def __init__(self, fail: bool = False):
        self._fail = fail
        self.alerts_sent = []

    def send_alert(self, text):
        self.alerts_sent.append(text)
        if self._fail:
            raise RuntimeError("slack webhook down")


_KB_ARTICLES = [
    Article(id="defect_process", title="Defect Process", content="Start a defect claim within 14 days."),
    Article(id="shipping_policy", title="Shipping Policy", content="Standard orders ship in 3-5 days."),
]


def _message(message_id="m1", subject="Broken part", body="It arrived cracked."):
    return EmailMessage(id=message_id, thread_id=f"t_{message_id}", subject=subject, sender="a@b.com", body=body)


def test_non_sensitive_high_confidence_message_gets_a_draft_and_monday_item():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="asking about order")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert len(results) == 1
    assert results[0].escalated is False
    assert results[0].status == "Draft Ready for Approval"
    assert len(gmail.created_drafts) == 1
    assert gmail.applied_labels == []
    assert gmail.marked_processed == ["m1"]
    assert len(monday.created_records) == 1
    assert monday.created_records[0].status == "Draft Ready for Approval"
    assert monday.created_records[0].gmail_draft_id == "draft_1"
    assert failures == []


def test_sensitive_intent_message_is_escalated_without_a_draft():
    claude = _FakeClaudeGateway(
        RawClassification(
            intent="defect_complaint", urgency="high", confidence=0.95, reasoning="broken part reported"
        )
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert results[0].escalated is True
    assert results[0].status == "Escalated - Needs Human"
    assert gmail.created_drafts == []
    assert gmail.applied_labels == [("m1", "Needs-Human")]
    assert monday.created_records[0].status == "Escalated - Needs Human"
    assert monday.created_records[0].gmail_draft_id == ""
    assert failures == []


def test_low_confidence_message_is_escalated_even_with_safe_intent():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.3, reasoning="unclear message")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert results[0].escalated is True
    assert gmail.applied_labels == [("m1", "Needs-Human")]
    assert failures == []


def test_processes_every_message_returned_by_the_gateway():
    claude = _FakeClaudeGateway(
        RawClassification(intent="quote_request", urgency="low", confidence=0.8, reasoning="asking for a quote")
    )
    gmail = _FakeGmailGateway(
        {
            "m1": _message("m1", "Quote please", "Need a quote"),
            "m2": _message("m2", "Another quote", "Need another quote"),
        }
    )
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert len(results) == 2
    assert gmail.marked_processed == ["m1", "m2"]
    assert failures == []


def test_every_processed_message_is_marked_processed_even_when_escalated():
    claude = _FakeClaudeGateway(
        RawClassification(intent="defect_complaint", urgency="high", confidence=0.9, reasoning="defect")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()

    _, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert gmail.marked_processed == ["m1"]
    assert failures == []


def test_one_message_failing_does_not_stop_the_rest_of_the_batch():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="asking about order"),
        fail_for_message_ids={"Fails here"},
    )
    gmail = _FakeGmailGateway(
        {
            "m1": _message("m1", "Fine subject 1", "body 1"),
            "m2": _message("m2", "Fails here", "this one blows up"),
            "m3": _message("m3", "Fine subject 3", "body 3"),
        }
    )
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert [r.gmail_message_id for r in results] == ["m1", "m3"]
    assert len(failures) == 1
    assert failures[0].gmail_message_id == "m2"
    assert "simulated transient failure" in failures[0].error


def test_a_failed_message_is_not_marked_processed_so_it_retries_next_run():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="ok"),
        fail_for_message_ids={"Fails here"},
    )
    gmail = _FakeGmailGateway({"m1": _message("m1", "Fails here", "body")})
    monday = _FakeMondayGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert gmail.marked_processed == []
    assert monday.created_records == []


def test_escalation_sends_a_slack_alert_with_subject_sender_and_reason():
    claude = _FakeClaudeGateway(
        RawClassification(intent="defect_complaint", urgency="high", confidence=0.95, reasoning="broken part")
    )
    gmail = _FakeGmailGateway({"m1": _message(subject="Cracked housing")})
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    assert len(slack.alerts_sent) == 1
    assert "Cracked housing" in slack.alerts_sent[0]
    assert "a@b.com" in slack.alerts_sent[0]


def test_non_escalated_run_sends_only_the_summary_alert_not_an_escalation_alert():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="ok")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    assert slack.alerts_sent == ["1 draft reply ready for review on the monday.com board."]


def test_no_alert_sent_at_all_when_no_slack_gateway_provided():
    claude = _FakeClaudeGateway(
        RawClassification(intent="defect_complaint", urgency="high", confidence=0.95, reasoning="broken part")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
    )

    assert results[0].escalated is True
    assert failures == []


def test_a_failing_slack_alert_does_not_fail_the_escalation_itself():
    claude = _FakeClaudeGateway(
        RawClassification(intent="defect_complaint", urgency="high", confidence=0.95, reasoning="broken part")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway(fail=True)

    results, failures = process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    assert failures == []
    assert results[0].escalated is True
    assert monday.created_records[0].status == "Escalated - Needs Human"
    assert gmail.marked_processed == ["m1"]


def test_summary_alert_covers_every_draft_created_in_the_run():
    claude = _FakeClaudeGateway(
        RawClassification(intent="quote_request", urgency="low", confidence=0.8, reasoning="asking for a quote")
    )
    gmail = _FakeGmailGateway(
        {
            "m1": _message("m1", "Quote please", "Need a quote"),
            "m2": _message("m2", "Another quote", "Need another quote"),
        }
    )
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    assert slack.alerts_sent == ["2 draft replies ready for review on the monday.com board."]


def test_failures_send_a_summary_alert_listing_each_one():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="ok"),
        fail_for_message_ids={"Fails here"},
    )
    gmail = _FakeGmailGateway(
        {
            "m1": _message("m1", "Fine subject", "body"),
            "m2": _message("m2", "Fails here", "this one blows up"),
        }
    )
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    failure_alerts = [a for a in slack.alerts_sent if "failed" in a]
    assert len(failure_alerts) == 1
    assert "1 message(s) failed" in failure_alerts[0]
    assert "m2" in failure_alerts[0]


def test_no_failure_alert_when_nothing_failed():
    claude = _FakeClaudeGateway(
        RawClassification(intent="order_status", urgency="low", confidence=0.9, reasoning="ok")
    )
    gmail = _FakeGmailGateway({"m1": _message()})
    monday = _FakeMondayGateway()
    slack = _FakeSlackGateway()

    process_new_messages(
        gmail_gateway=gmail,
        llm_gateway=claude,
        monday_gateway=monday,
        kb_articles=_KB_ARTICLES,
        confidence_threshold=0.6,
        slack_gateway=slack,
    )

    assert not any("failed" in a for a in slack.alerts_sent)
