"""One-time migration: reads the local data/kb_articles.json file and
upserts every article into the Supabase kb_articles table. Safe to
re-run; upserts on id, so it never creates duplicates.

Usage: python -m scripts.migrate_kb_to_supabase
"""

import requests

from app.config import load_settings
from app.errors import GatewayError
from app.gateways.knowledge_base_repo import load_articles


def main() -> None:
    settings = load_settings()
    articles = load_articles()

    rows = [{"id": a.id, "title": a.title, "content": a.content} for a in articles]

    response = requests.post(
        f"{settings.supabase_url.rstrip('/')}/rest/v1/kb_articles",
        headers={
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        json=rows,
    )

    if response.status_code not in (200, 201):
        raise GatewayError("supabase", f"Migration failed: {response.status_code}: {response.text}")

    print(f"Upserted {len(response.json())} article(s) into Supabase.")


if __name__ == "__main__":
    main()
