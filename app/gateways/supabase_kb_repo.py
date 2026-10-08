"""Reads the knowledge-base articles from Supabase's auto-generated
REST API (PostgREST) instead of a local file, so the knowledge base
lives somewhere a real team could view and edit, not just on one
machine. Uses the service_role key, which bypasses row-level security,
since this is a backend script, never a browser client."""

import requests

from app.errors import GatewayError
from app.gateways.knowledge_base_repo import Article

TABLE = "kb_articles"


class SupabaseKBRepo:
    def __init__(self, url: str, service_key: str, http_get=requests.get):
        self._base_url = url.rstrip("/")
        self._service_key = service_key
        self._http_get = http_get

    def load_articles(self) -> list[Article]:
        try:
            response = self._http_get(
                f"{self._base_url}/rest/v1/{TABLE}",
                headers={
                    "apikey": self._service_key,
                    "Authorization": f"Bearer {self._service_key}",
                },
                params={"select": "id,title,content", "order": "id"},
            )
        except Exception as exc:
            raise GatewayError("supabase", f"Loading KB articles failed: {exc}") from exc

        if response.status_code != 200:
            raise GatewayError(
                "supabase", f"Supabase returned {response.status_code}: {response.text}"
            )

        try:
            rows = response.json()
        except ValueError as exc:
            raise GatewayError("supabase", f"Supabase response was not valid JSON: {exc}") from exc

        try:
            return [Article(id=r["id"], title=r["title"], content=r["content"]) for r in rows]
        except (KeyError, TypeError) as exc:
            raise GatewayError("supabase", f"KB row missing a required field: {exc}") from exc
