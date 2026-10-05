"""The only place that talks to the Gmail API. Everything is scoped to
one label, read via Gmail's search query syntax, never a raw inbox scan.
The service layer never sees the raw Gmail message shape, only
EmailMessage."""

import base64
from dataclasses import dataclass
from email.mime.text import MIMEText

from app.errors import GatewayError


@dataclass(frozen=True)
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    sender: str
    body: str


class GmailGateway:
    def __init__(self, service, label: str, processed_label: str, escalation_label: str):
        self._service = service
        self._label = label
        self._processed_label = processed_label
        self._escalation_label = escalation_label
        self._label_id_cache: dict[str, str] = {}

    @property
    def escalation_label(self) -> str:
        return self._escalation_label

    def list_new_message_ids(self) -> list[str]:
        query = f"label:{self._label} -label:{self._processed_label}"
        try:
            result = (
                self._service.users()
                .messages()
                .list(userId="me", q=query)
                .execute()
            )
        except Exception as exc:
            raise GatewayError("gmail", f"Listing messages failed: {exc}") from exc

        return [m["id"] for m in result.get("messages", [])]

    def get_message(self, message_id: str) -> EmailMessage:
        try:
            raw = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except Exception as exc:
            raise GatewayError("gmail", f"Fetching message {message_id} failed: {exc}") from exc

        payload = raw.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        return EmailMessage(
            id=raw["id"],
            thread_id=raw["threadId"],
            subject=headers.get("Subject", ""),
            sender=headers.get("From", ""),
            body=_extract_plain_text_body(payload),
        )

    def mark_processed(self, message_id: str) -> None:
        self.apply_label(message_id, self._processed_label)

    def apply_label(self, message_id: str, label_name: str) -> None:
        label_id = self._ensure_label_id(label_name)
        try:
            self._service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id], "removeLabelIds": []},
            ).execute()
        except Exception as exc:
            raise GatewayError(
                "gmail", f"Applying label {label_name!r} to {message_id} failed: {exc}"
            ) from exc

    def create_draft(self, thread_id: str, to: str, subject: str, body_text: str) -> str:
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        mime_message = MIMEText(body_text)
        mime_message["To"] = to
        mime_message["Subject"] = reply_subject

        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("ascii")
        body = {"message": {"raw": raw, "threadId": thread_id}}

        try:
            result = self._service.users().drafts().create(userId="me", body=body).execute()
        except Exception as exc:
            raise GatewayError(
                "gmail", f"Creating draft on thread {thread_id} failed: {exc}"
            ) from exc

        return result["id"]

    def insert_message(
        self, sender: str, to: str, subject: str, body_text: str, label_names: list[str]
    ) -> str:
        """Inserts a message directly into the mailbox (not a real SMTP
        send). Used only by the setup script to seed synthetic test data."""
        label_ids = [self._ensure_label_id(name) for name in label_names]

        mime_message = MIMEText(body_text)
        mime_message["From"] = sender
        mime_message["To"] = to
        mime_message["Subject"] = subject

        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("ascii")
        body = {"raw": raw, "labelIds": label_ids}

        try:
            result = self._service.users().messages().insert(userId="me", body=body).execute()
        except Exception as exc:
            raise GatewayError("gmail", f"Inserting message failed: {exc}") from exc

        return result["id"]

    def _ensure_label_id(self, label_name: str) -> str:
        if label_name in self._label_id_cache:
            return self._label_id_cache[label_name]

        try:
            result = self._service.users().labels().list(userId="me").execute()
        except Exception as exc:
            raise GatewayError("gmail", f"Listing labels failed: {exc}") from exc

        for label in result.get("labels", []):
            self._label_id_cache[label["name"]] = label["id"]

        if label_name in self._label_id_cache:
            return self._label_id_cache[label_name]

        try:
            created = (
                self._service.users()
                .labels()
                .create(userId="me", body={"name": label_name})
                .execute()
            )
        except Exception as exc:
            raise GatewayError("gmail", f"Creating label {label_name!r} failed: {exc}") from exc

        self._label_id_cache[label_name] = created["id"]
        return created["id"]


def _extract_plain_text_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                return _decode(part["body"]["data"])
        for part in payload["parts"]:
            if "data" in part.get("body", {}):
                return _decode(part["body"]["data"])
        return ""

    data = payload.get("body", {}).get("data")
    return _decode(data) if data else ""


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
