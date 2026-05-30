"""Write-scope gating and confirmation token handling."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import get_config


class WritesNotEnabledError(RuntimeError):
    """Raised when a write tool is called without --allow-writes."""


class InvalidConfirmationTokenError(ValueError):
    """Raised when a destructive call supplies the wrong confirmation token."""


def require_writes() -> None:
    """Call at the top of every write tool. Raises if writes are disabled."""
    if not get_config().allow_writes:
        raise WritesNotEnabledError(
            "Write operations are disabled. Start the server with --allow-writes to enable them."
        )


def make_confirmation_token(operation: str, params: dict[str, Any]) -> str:
    """Return a short token the caller must echo back to confirm a destructive op.

    The token encodes the operation + params so that a confirmation for 'stop
    i-abc123' can't be reused for 'stop i-xyz999'.
    """
    payload = json.dumps({"op": operation, "params": params}, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"confirm-{operation}-{digest}"


def verify_confirmation_token(operation: str, params: dict[str, Any], token: str) -> None:
    """Raise InvalidConfirmationTokenError if token doesn't match."""
    expected = make_confirmation_token(operation, params)
    if token != expected:
        raise InvalidConfirmationTokenError(f"Confirmation token mismatch. Expected: {expected}")
