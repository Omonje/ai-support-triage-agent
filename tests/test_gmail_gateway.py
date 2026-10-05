import base64

import pytest

from app.errors import GatewayError
from app.gateways.gmail_gateway import GmailGateway


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


class _FakeExecutor:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def execute(self):
        if self._exc:
            raise self._exc
        return self._result


class _FakeMessagesResource:
    def __init__(self, list_result=None, get_results=None, list_exc=None):
        self._list_result = list_result or {"messages": []}
        self._get_results = get_results or {}
        self._list_exc = list_exc
        self.list_calls = []
        self.modify_calls = []

    def list(self, userId, q, **kwargs):
        self.list_calls.append(q)
        return _FakeExecutor(self._list_result, exc=self._list_exc)

    def get(self, userId, id, format="full"):
        return _FakeExecutor(self._get_results[id])

    def modify(self, userId, id, body):
        self.modify_calls.append((id, body))
        return _FakeExecutor({"id": id})


class _FakeDraftsResource:
    def __init__(self, exc=None):
        self._exc = exc
        self.create_calls = []

    def create(self, userId, body):
        self.create_calls.append(body)
        return _FakeExecutor({"id": "draft_1"}, exc=self._exc)


class _FakeLabelsResource:
    def __init__(self, existing_labels=None):
        self._labels = existing_labels or []
        self.create_calls = []

    def list(self, userId):
        return _FakeExecutor({"labels": self._labels})

    def create(self, userId, body):
        new_label = {"id": f"id_for_{body['name']}", "name": body["name"]}
        self._labels.append(new_label)
        self.create_calls.append(body["name"])
        return _FakeExecutor(new_label)


class _FakeUsers:
    def __init__(self, messages_resource, labels_resource, drafts_resource):
        self._messages = messages_resource
        self._labels = labels_resource
        self._drafts = drafts_resource

    def messages(self):
        return self._messages

    def labels(self):
        return self._labels

    def drafts(self):
        return self._drafts


class _FakeService:
    def __init__(self, messages_resource=None, labels_resource=None, drafts_resource=None):
        self._users = _FakeUsers(
            messages_resource or _FakeMessagesResource(),
            labels_resource or _FakeLabelsResource(existing_labels=[{"id": "Label_1", "name": "Triage-Demo"}]),
            drafts_resource or _FakeDraftsResource(),
        )

    def users(self):
        return self._users


def _gateway(service=None):
    return GmailGateway(
        service or _FakeService(),
        label="Triage-Demo",
        processed_label="Processed",
        escalation_label="Needs-Human",
    )


def test_list_new_message_ids_queries_label_and_excludes_processed():
    messages_resource = _FakeMessagesResource(list_result={"messages": [{"id": "m1"}, {"id": "m2"}]})
    service = _FakeService(messages_resource=messages_resource)
    gateway = _gateway(service)

    ids = gateway.list_new_message_ids()

    assert ids == ["m1", "m2"]
    assert messages_resource.list_calls == ["label:Triage-Demo -label:Processed"]


def test_list_new_message_ids_returns_empty_list_when_none_found():
    service = _FakeService(messages_resource=_FakeMessagesResource(list_result={}))
    gateway = _gateway(service)

    assert gateway.list_new_message_ids() == []


def test_list_new_message_ids_raises_gateway_error_on_api_failure():
    service = _FakeService(messages_resource=_FakeMessagesResource(list_exc=RuntimeError("down")))
    gateway = _gateway(service)

    with pytest.raises(GatewayError):
        gateway.list_new_message_ids()


def test_get_message_parses_single_part_body():
    payload = {
        "headers": [
            {"name": "Subject", "value": "Broken part"},
            {"name": "From", "value": "customer@example.com"},
        ],
        "mimeType": "text/plain",
        "body": {"data": _b64("The part arrived cracked.")},
    }
    messages_resource = _FakeMessagesResource(get_results={"m1": {"id": "m1", "threadId": "t1", "payload": payload}})
    gateway = _gateway(_FakeService(messages_resource=messages_resource))

    message = gateway.get_message("m1")

    assert message.id == "m1"
    assert message.thread_id == "t1"
    assert message.subject == "Broken part"
    assert message.sender == "customer@example.com"
    assert message.body == "The part arrived cracked."


def test_get_message_parses_multipart_prefers_text_plain():
    payload = {
        "headers": [{"name": "Subject", "value": "Quote request"}, {"name": "From", "value": "a@b.com"}],
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/html", "body": {"data": _b64("<p>html</p>")}},
            {"mimeType": "text/plain", "body": {"data": _b64("plain text body")}},
        ],
    }
    messages_resource = _FakeMessagesResource(get_results={"m2": {"id": "m2", "threadId": "t2", "payload": payload}})
    gateway = _gateway(_FakeService(messages_resource=messages_resource))

    message = gateway.get_message("m2")

    assert message.body == "plain text body"


def test_mark_processed_adds_processed_label():
    messages_resource = _FakeMessagesResource()
    labels_resource = _FakeLabelsResource(
        existing_labels=[{"id": "Label_1", "name": "Triage-Demo"}, {"id": "Label_2", "name": "Processed"}]
    )
    gateway = _gateway(_FakeService(messages_resource=messages_resource, labels_resource=labels_resource))

    gateway.mark_processed("m1")

    assert messages_resource.modify_calls == [("m1", {"addLabelIds": ["Label_2"], "removeLabelIds": []})]


def test_ensure_label_creates_missing_label():
    labels_resource = _FakeLabelsResource(existing_labels=[{"id": "Label_1", "name": "Triage-Demo"}])
    gateway = _gateway(_FakeService(labels_resource=labels_resource))

    gateway.mark_processed("m1")

    assert labels_resource.create_calls == ["Processed"]


def test_ensure_label_reuses_existing_label_without_creating():
    labels_resource = _FakeLabelsResource(
        existing_labels=[{"id": "Label_1", "name": "Triage-Demo"}, {"id": "Label_2", "name": "Processed"}]
    )
    gateway = _gateway(_FakeService(labels_resource=labels_resource))

    gateway.mark_processed("m1")

    assert labels_resource.create_calls == []


def test_apply_label_adds_the_named_label():
    messages_resource = _FakeMessagesResource()
    labels_resource = _FakeLabelsResource(
        existing_labels=[{"id": "Label_1", "name": "Triage-Demo"}, {"id": "Label_3", "name": "Needs-Human"}]
    )
    gateway = _gateway(_FakeService(messages_resource=messages_resource, labels_resource=labels_resource))

    gateway.apply_label("m1", "Needs-Human")

    assert messages_resource.modify_calls == [("m1", {"addLabelIds": ["Label_3"], "removeLabelIds": []})]


def test_create_draft_sends_the_thread_id_and_returns_the_draft_id():
    drafts_resource = _FakeDraftsResource()
    gateway = _gateway(_FakeService(drafts_resource=drafts_resource))

    draft_id = gateway.create_draft(
        thread_id="t1", to="customer@example.com", subject="Broken part", body_text="Thanks for reaching out."
    )

    assert draft_id == "draft_1"
    assert len(drafts_resource.create_calls) == 1
    sent_body = drafts_resource.create_calls[0]
    assert sent_body["message"]["threadId"] == "t1"
    assert "raw" in sent_body["message"]


def test_create_draft_prefixes_subject_with_re_when_missing():
    drafts_resource = _FakeDraftsResource()
    gateway = _gateway(_FakeService(drafts_resource=drafts_resource))

    gateway.create_draft(thread_id="t1", to="a@b.com", subject="Broken part", body_text="body")

    raw = drafts_resource.create_calls[0]["message"]["raw"]
    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8")
    assert "Subject: Re: Broken part" in decoded


def test_create_draft_does_not_double_prefix_an_existing_re_subject():
    drafts_resource = _FakeDraftsResource()
    gateway = _gateway(_FakeService(drafts_resource=drafts_resource))

    gateway.create_draft(thread_id="t1", to="a@b.com", subject="Re: Broken part", body_text="body")

    raw = drafts_resource.create_calls[0]["message"]["raw"]
    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8")
    assert "Subject: Re: Broken part" in decoded
    assert "Re: Re:" not in decoded


def test_create_draft_raises_gateway_error_on_api_failure():
    drafts_resource = _FakeDraftsResource(exc=RuntimeError("down"))
    gateway = _gateway(_FakeService(drafts_resource=drafts_resource))

    with pytest.raises(GatewayError):
        gateway.create_draft(thread_id="t1", to="a@b.com", subject="subj", body_text="body")
