"""Structured logging. Never log secrets or message content, only ids,
classifications, and decisions, so logs are safe to share for debugging."""

import logging
import sys


def configure_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """log_file is optional: pass it for a script (like run_pipeline.py)
    that should leave a durable record behind, not just console output
    that's gone once the terminal scrolls past it or closes. Omit it
    (the default) for something already monitored another way, like the
    FastAPI app's own request logs."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)r}',
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
