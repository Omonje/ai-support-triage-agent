"""The only place that reads the knowledge-base articles from disk. The
service layer never touches the file system directly."""

import json
from dataclasses import dataclass
from pathlib import Path

from app.errors import GatewayError

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "kb_articles.json"


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    content: str


def load_articles(path: Path | None = None) -> list[Article]:
    target = path or _DEFAULT_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GatewayError("knowledge_base", f"KB file not found at {target}") from exc
    except json.JSONDecodeError as exc:
        raise GatewayError("knowledge_base", f"KB file at {target} is not valid JSON: {exc}") from exc

    try:
        return [Article(id=a["id"], title=a["title"], content=a["content"]) for a in raw]
    except (KeyError, TypeError) as exc:
        raise GatewayError(
            "knowledge_base", f"KB file at {target} has an article missing a required field: {exc}"
        ) from exc
