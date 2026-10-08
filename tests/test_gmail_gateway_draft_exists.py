import pytest
from googleapiclient.errors import HttpError

from app.errors import GatewayError
from app.gateways.gmail_gateway import GmailGateway


class _FakeResp:
    def __init__(self, status):
        self.status = status
        self.reason = "error"


class _FakeDraftsResource:
    def __init__(self, exists=True, http_status=None, other_exc=None, message_label_ids=None):
        self._exists = exists
        self._http_status = http_status
        self._other_exc = other_exc
        self._message_label_ids = message_label_ids if message_label_ids is not None else ["DRAFT"]
        self.get_calls = []

    def get(self, userId, id):
        self.get_calls.append(id)

        class _Exec:
            def __init__(self, outer):
                self._outer = outer

            def execute(self):
                if self._outer._other_exc:
                    raise self._outer._other_exc
                if self._outer._http_status is not None:
                    raise HttpError(_FakeResp(self._outer._http_status), b"error body")
                return {
                    "id": self._outer.get_calls[-1],
                    "message": {"id": "msg_1", "labelIds": self._outer._message_label_ids},
                }

        return _Exec(self)


class _FakeUsersForDraftExists:
    def __init__(self, drafts_resource):
        self._drafts = drafts_resource

    def drafts(self):
        return self._drafts

    def messages(self):
        raise NotImplementedError

    def labels(self):
        raise NotImplementedError


class _FakeServiceForDraftExists:
    def __init__(self, drafts_resource):
        self._users = _FakeUsersForDraftExists(drafts_resource)

    def users(self):
        return self._users


def _gateway(drafts_resource):
    return GmailGateway(
        _FakeServiceForDraftExists(drafts_resource),
        label="Triage-Demo",
        processed_label="Processed",
        escalation_label="Needs-Human",
    )


def test_draft_exists_returns_true_when_the_draft_is_still_there():
    gateway = _gateway(_FakeDraftsResource(exists=True))

    assert gateway.draft_exists("draft_1") is True


def test_draft_exists_returns_false_on_a_404():
    gateway = _gateway(_FakeDraftsResource(http_status=404))

    assert gateway.draft_exists("draft_1") is False


def test_draft_exists_returns_false_when_the_underlying_message_was_already_sent():
    """Regression test: sending a draft from inside Gmail's own draft view
    does not make drafts.get() 404, it keeps succeeding and just returns
    the now-sent message, with 'SENT' in its labels and no 'DRAFT'. Caught
    2026-10-08 against a real sent draft (LOG.md): the 404-only check
    reported every sent draft as still pending."""
    gateway = _gateway(_FakeDraftsResource(message_label_ids=["SENT", "INBOX"]))

    assert gateway.draft_exists("draft_1") is False


def test_draft_exists_raises_gateway_error_on_a_non_404_http_error():
    gateway = _gateway(_FakeDraftsResource(http_status=500))

    with pytest.raises(GatewayError):
        gateway.draft_exists("draft_1")


def test_draft_exists_raises_gateway_error_on_other_failures():
    gateway = _gateway(_FakeDraftsResource(other_exc=RuntimeError("network down")))

    with pytest.raises(GatewayError):
        gateway.draft_exists("draft_1")
