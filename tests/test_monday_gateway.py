import json

import pytest

from app.errors import GatewayError
from app.gateways.monday_gateway import MondayGateway, TriageRecord


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeHttpPost:
    def __init__(self, response_payload=None, exc=None):
        self._response_payload = response_payload
        self._exc = exc
        self.calls = []

    def __call__(self, url, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        if self._exc:
            raise self._exc
        return _FakeResponse(self._response_payload)


def _record(**overrides):
    defaults = dict(
        gmail_message_id="m1",
        item_name="Broken part - customer@example.com",
        status="Draft Ready for Approval",
        intent="defect_complaint",
        urgency="high",
        confidence=0.92,
        kb_articles_used="defect_process",
        reasoning="customer reports a cracked part",
        processed_at="2026-10-05",
        gmail_draft_id="draft_1",
    )
    defaults.update(overrides)
    return TriageRecord(**defaults)


def test_create_item_returns_the_new_item_id():
    http_post = _FakeHttpPost(response_payload={"data": {"create_item": {"id": "item_1"}}})
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    item_id = gateway.create_item(_record())

    assert item_id == "item_1"
    assert http_post.calls[0]["headers"]["Authorization"] == "token"


def test_create_item_sends_expected_column_values():
    http_post = _FakeHttpPost(response_payload={"data": {"create_item": {"id": "item_1"}}})
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    gateway.create_item(_record())

    variables = http_post.calls[0]["json"]["variables"]
    column_values = json.loads(variables["columnValues"])
    assert column_values["color_mm7tjn17"] == {"label": "Draft Ready for Approval"}
    assert column_values["numeric_mm7tgk70"] == 0.92
    assert column_values["text_mm7tn406"] == "m1"


def test_create_item_raises_gateway_error_on_api_errors_field():
    http_post = _FakeHttpPost(response_payload={"errors": [{"message": "board not found"}]})
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="bad_id")

    with pytest.raises(GatewayError):
        gateway.create_item(_record())


def test_create_item_raises_gateway_error_on_transport_failure():
    http_post = _FakeHttpPost(exc=RuntimeError("timeout"))
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    with pytest.raises(GatewayError):
        gateway.create_item(_record())


def test_update_item_status_sends_the_new_status_label():
    http_post = _FakeHttpPost(response_payload={"data": {"change_multiple_column_values": {"id": "item_1"}}})
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    gateway.update_item_status("item_1", "Sent")

    variables = http_post.calls[0]["json"]["variables"]
    column_values = json.loads(variables["columnValues"])
    assert column_values["color_mm7tjn17"] == {"label": "Sent"}


def test_update_item_status_raises_gateway_error_on_failure():
    http_post = _FakeHttpPost(exc=RuntimeError("down"))
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    with pytest.raises(GatewayError):
        gateway.update_item_status("item_1", "Sent")


def test_list_items_with_status_returns_item_id_and_draft_id():
    http_post = _FakeHttpPost(
        response_payload={
            "data": {
                "boards": [
                    {
                        "items_page": {
                            "items": [
                                {
                                    "id": "item_1",
                                    "column_values": [
                                        {"id": "color_mm7tjn17", "text": "Draft Ready for Approval"},
                                        {"id": "text_mm7tsys9", "text": "draft_a"},
                                    ],
                                },
                                {
                                    "id": "item_2",
                                    "column_values": [
                                        {"id": "color_mm7tjn17", "text": "Draft Ready for Approval"},
                                        {"id": "text_mm7tsys9", "text": "draft_b"},
                                    ],
                                },
                            ]
                        }
                    }
                ]
            }
        }
    )
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    items = gateway.list_items_with_status("Draft Ready for Approval")

    assert items == [
        {"item_id": "item_1", "gmail_draft_id": "draft_a"},
        {"item_id": "item_2", "gmail_draft_id": "draft_b"},
    ]


def test_list_items_with_status_filters_out_items_with_a_different_status():
    """Regression test: monday's own query_params status filter needs the
    internal numeric index, not the label text, so filtering must happen
    client-side on the returned text instead. Caught 2026-10-08 when a real
    board with real items of mixed status came back empty despite matching
    items existing (DECISIONS.md, LOG.md)."""
    http_post = _FakeHttpPost(
        response_payload={
            "data": {
                "boards": [
                    {
                        "items_page": {
                            "items": [
                                {
                                    "id": "item_1",
                                    "column_values": [
                                        {"id": "color_mm7tjn17", "text": "Draft Ready for Approval"},
                                        {"id": "text_mm7tsys9", "text": "draft_a"},
                                    ],
                                },
                                {
                                    "id": "item_2",
                                    "column_values": [
                                        {"id": "color_mm7tjn17", "text": "Escalated - Needs Human"},
                                        {"id": "text_mm7tsys9", "text": "draft_b"},
                                    ],
                                },
                                {
                                    "id": "item_3",
                                    "column_values": [
                                        {"id": "color_mm7tjn17", "text": "Draft Ready for Approval"},
                                        {"id": "text_mm7tsys9", "text": "draft_c"},
                                    ],
                                },
                            ]
                        }
                    }
                ]
            }
        }
    )
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    items = gateway.list_items_with_status("Draft Ready for Approval")

    assert items == [
        {"item_id": "item_1", "gmail_draft_id": "draft_a"},
        {"item_id": "item_3", "gmail_draft_id": "draft_c"},
    ]


def test_list_items_with_status_returns_empty_list_when_board_not_found():
    http_post = _FakeHttpPost(response_payload={"data": {"boards": []}})
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    assert gateway.list_items_with_status("Draft Ready for Approval") == []


def test_list_items_with_status_raises_gateway_error_on_failure():
    http_post = _FakeHttpPost(exc=RuntimeError("down"))
    gateway = MondayGateway(http_post=http_post, api_token="token", board_id="18433915127")

    with pytest.raises(GatewayError):
        gateway.list_items_with_status("Draft Ready for Approval")
