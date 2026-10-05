"""The only place that talks to the monday.com API. Column IDs are fixed
for the Support Triage Queue board created for this project (see
DECISIONS.md #4), not meant to be reconfigured per deployment."""

import json as json_module
from dataclasses import dataclass

import requests

from app.errors import GatewayError

API_URL = "https://api.monday.com/v2"

COLUMN_STATUS = "color_mm7tjn17"
COLUMN_INTENT = "color_mm7tfbz2"
COLUMN_URGENCY = "color_mm7t8wpv"
COLUMN_CONFIDENCE = "numeric_mm7tgk70"
COLUMN_GMAIL_MESSAGE_ID = "text_mm7tn406"
COLUMN_GMAIL_DRAFT_ID = "text_mm7tsys9"
COLUMN_KB_ARTICLES_USED = "text_mm7t7ccn"
COLUMN_REASONING = "long_text_mm7trma5"
COLUMN_PROCESSED_AT = "date_mm7tca2s"

_CREATE_ITEM_MUTATION = """
mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
  create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
    id
  }
}
"""

_UPDATE_STATUS_MUTATION = """
mutation ($boardId: ID!, $itemId: ID!, $columnValues: JSON!) {
  change_multiple_column_values(board_id: $boardId, item_id: $itemId, column_values: $columnValues) {
    id
  }
}
"""


@dataclass(frozen=True)
class TriageRecord:
    gmail_message_id: str
    item_name: str
    status: str
    intent: str
    urgency: str
    confidence: float
    kb_articles_used: str
    reasoning: str
    processed_at: str  # ISO date, "YYYY-MM-DD"
    gmail_draft_id: str = ""


class MondayGateway:
    def __init__(self, api_token: str, board_id: str, http_post=requests.post):
        self._api_token = api_token
        self._board_id = board_id
        self._http_post = http_post

    def create_item(self, record: TriageRecord) -> str:
        column_values = {
            COLUMN_STATUS: {"label": record.status},
            COLUMN_INTENT: {"label": record.intent},
            COLUMN_URGENCY: {"label": record.urgency},
            COLUMN_CONFIDENCE: record.confidence,
            COLUMN_GMAIL_MESSAGE_ID: record.gmail_message_id,
            COLUMN_GMAIL_DRAFT_ID: record.gmail_draft_id,
            COLUMN_KB_ARTICLES_USED: record.kb_articles_used,
            COLUMN_REASONING: record.reasoning,
            COLUMN_PROCESSED_AT: {"date": record.processed_at},
        }

        variables = {
            "boardId": self._board_id,
            "itemName": record.item_name,
            "columnValues": json_module.dumps(column_values),
        }

        data = self._execute(_CREATE_ITEM_MUTATION, variables)
        return data["create_item"]["id"]

    def update_item_status(self, item_id: str, status: str, gmail_draft_id: str | None = None) -> None:
        column_values = {COLUMN_STATUS: {"label": status}}
        if gmail_draft_id is not None:
            column_values[COLUMN_GMAIL_DRAFT_ID] = gmail_draft_id

        variables = {
            "boardId": self._board_id,
            "itemId": item_id,
            "columnValues": json_module.dumps(column_values),
        }

        self._execute(_UPDATE_STATUS_MUTATION, variables)

    def _execute(self, query: str, variables: dict) -> dict:
        try:
            response = self._http_post(
                API_URL,
                headers={"Authorization": self._api_token, "Content-Type": "application/json"},
                json={"query": query, "variables": variables},
            )
        except Exception as exc:
            raise GatewayError("monday", f"API call failed: {exc}") from exc

        payload = response.json()
        if "errors" in payload:
            raise GatewayError("monday", f"API returned errors: {payload['errors']}")

        return payload["data"]
