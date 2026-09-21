"""Request id propagation via a context variable (used by logging and error responses)."""

import re
import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"
_VALID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> str:
    """Store a client-supplied id if it is well-formed, otherwise generate one."""
    rid = value if value and _VALID.match(value) else uuid.uuid4().hex
    _request_id.set(rid)
    return rid


def clear_request_id() -> None:
    _request_id.set(None)
