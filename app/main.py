"""Entry layer. Decides nothing: loads config, wires it up, formats
responses. All real logic lives in app/service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import load_settings
from app.errors import ConfigError
from app.logging_setup import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

_settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _settings
    try:
        _settings = load_settings()
    except ConfigError as exc:
        logger.error("Startup config check failed: %s", exc.message)
        raise
    yield


app = FastAPI(title="AI Support Triage Agent", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "configured": _settings is not None}
