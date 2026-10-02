"""Two kinds of error: expected ones (a code and a safe message a human can
act on) and bugs (a generic message plus a reference number; details only
go to the log, never to a caller)."""

import uuid


class TriageError(Exception):
    """An expected failure. Safe to show its message to a human."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ConfigError(TriageError):
    """Raised at startup when required configuration is missing or invalid."""

    def __init__(self, message: str):
        super().__init__("CONFIG_ERROR", message)


class GatewayError(TriageError):
    """An outside system (Gmail, monday.com, Claude) failed or refused a call."""

    def __init__(self, system: str, message: str):
        super().__init__(f"{system.upper()}_GATEWAY_ERROR", message)


def reference_number() -> str:
    """A short id to hand to a human when we can't explain a bug safely."""
    return uuid.uuid4().hex[:8]
