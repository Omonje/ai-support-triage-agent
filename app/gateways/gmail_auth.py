"""Builds the real Gmail API service object: loads a cached OAuth token
if one exists, refreshes it if expired, or runs the one-time interactive
consent flow if not. The only place that touches credentials.json or the
token cache file."""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.errors import GatewayError

# modify covers read, labels, and drafts; it excludes permanent delete and
# account settings changes, deliberately narrower than the full mail.google.com scope.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def build_gmail_service(oauth_client_path: str, token_cache_path: str):
    token_path = Path(token_cache_path)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_path = Path(oauth_client_path)
            if not client_path.exists():
                raise GatewayError(
                    "gmail",
                    f"OAuth client file not found at {client_path}. Download it from "
                    "Google Cloud Console (Desktop app type) and save it there.",
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)
