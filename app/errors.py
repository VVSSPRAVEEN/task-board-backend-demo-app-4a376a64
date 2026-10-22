"""Single error contract for the Task Board API.

Every failure path of the service is rendered with exactly one body shape::

    {"error": {"code": "<str>", "message": "<str>"}}

This module is deliberately dependency-light and side-effect free: it defines
the :class:`ErrorCode` enum, the immutable ``code -> HTTP status`` map, the
pure :func:`error_payload` builder and the domain exceptions that the domain and
storage layers raise.  Nothing here imports FastAPI, so it stays unit
testable without an application instance and cannot leak framework internals
into the payload.

Security rules enforced here (see ``app/main.py`` for the translation): never
 emit tracebacks, SQL statements, driver messages or absolute filesystem
paths.  :func:`safe_message` is the single choke point that decides whether a
message may be shown to a client; :func:`sanitize_text` backs the test suite's
forbidden-substring rules.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "DEFAULT_MESSAGES",
    "FORBIDDEN_SUBSTRINGS",
    "REQUEST_METHODS_WITH_BODY",
    "STATUS_FOR_CODE",
    "AppError",
    "ErrorCode",
    "ResourceNotFound",
    "StorageUnavailableError",
    "ValidationFailed",
    "contains_forbidden_detail",
    "error_payload",
    "safe_message",
    "sanitize_text",
    "status_for",
]


class ErrorCode(StrEnum):
    """Canonical machine-readable error identifiers of the public contract."""

    INVALID_JSON = "invalid_json"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    INTERNAL_ERROR = "internal_error"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: Frozen ``code -> HTTP status`` map.  The public contract is:
#: invalid_json 400, not_found 404, validation_error 422,
#: unsupported_media_type 415, payload_too_large 413,
#: storage_unavailable 503, internal_error 500.
STATUS_FOR_CODE: Mapping[str, int] = {
    ErrorCode.INVALID_JSON.value: 400,
    ErrorCode.NOT_FOUND.value: 404,
    ErrorCode.UNSUPPORTED_MEDIA_TYPE.value: 415,
    ErrorCode.PAYLOAD_TOO_LARGE.value: 413,
    ErrorCode.VALIDATION_ERROR.value: 422,
    ErrorCode.INTERNAL_ERROR.value: 500,
    ErrorCode.STORAGE_UNAVAILABLE.value: 503,
}

#: Operator-facing defaults, free of internal detail by construction.
DEFAULT_MESSAGES: Mapping[str, str] = {
    ErrorCode.INVALID_JSON.value: "Request body must be valid JSON.",
    ErrorCode.NOT_FOUND.value: "The requested resource does not exist.",
    ErrorCode.VALIDATION_ERROR.value: "The request payload failed validation.",
    ErrorCode.STORAGE_UNAVAILABLE.value: "The task store is temporarily unavailable.",
    ErrorCode.UNSUPPORTED_MEDIA_TYPE.value: "Content-Type must be application/json.",
    ErrorCode.PAYLOAD_TOO_LARGE.value: "Request body exceeds the maximum allowed size.",
    ErrorCode.INTERNAL_ERROR.value: "An unexpected internal error occurred.",
}

#: Request methods that may carry a body; only these are shape-guarded.
REQUEST_METHODS_WITH_BODY = frozenset({"POST", "PUT", "PATCH", "DELETE"})

#: Substrings that must never reach a client response (body or header).
FORBIDDEN_SUBSTRINGS = (
    "Traceback",
    "SELECT ",
    "sqlite3.",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "PRAGMA",
    "sqlalchemy",
    "/generated/",
    "site-packages",
)

_ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s'\"(])(/[A-Za-z0-9_.\-]+){2,}")
_INTERNAL_RE = re.compile(
    r"(?i)\b(traceback|sql|sqlite|sqlite3|psycopg|sqlalchemy|\.py\"|\.py'|\.py\b"
    r"|errno|exception|stack ?trace|internal)"
)


def sanitize_text(value: str) -> str:
    """Return ``value`` with the repository path prefix removed.

    Used by the test suite (and by the log side of the handler) so an error
    string that happens to mention this checkout cannot travel to a client.
    """

    if not value:
        return ""
    cleaned = value.replace(str(_repo_root()), "")
    return cleaned.replace("/app/", "")


def _repo_root() -> str:
    """Absolute path of the project root (the parent of the ``app`` package)."""

    try:
        from pathlib import Path

        return str(Path(__file__).resolve().parent.parent)
    except Exception:  # pragma: no cover - defensive only
        return "/"


def contains_forbidden_detail(value: str) -> bool:
    """True when ``value`` carries a traceback, a SQL statement or a path."""

    if not value:
        return False
    lowered = value.lower()
    if "traceback" in lowered:
        return True
    if "sqlite3." in lowered:
        return True
    if "select " in lowered:
        return True
    if _ABSOLUTE_PATH_RE.search(value):
        return True
    return bool(_INTERNAL_RE.search(value))


def status_for(code: Any) -> int:
    """Return the HTTP status bound to ``code`` (500 for unknown input)."""

    value = code.value if isinstance(code, ErrorCode) else str(code)
    return STATUS_FOR_CODE.get(value, STATUS_FOR_CODE[ErrorCode.INTERNAL_ERROR.value])


def error_payload(code: Any, message: str | None = None) -> dict[str, dict[str, str]]:
    """Purely build the canonical envelope for ``code``.

    The result is always ``{"error": {"code": ..., "message": ...}}`` with no
    ``detail`` key and no additional top-level key.  ``message`` is trimmed to
    a single line and length-capped; anything that looks like internal detail is
    replaced by the code's default message.
    """

    value = code.value if isinstance(code, ErrorCode) else str(code)
    fallback = DEFAULT_MESSAGES.get(value, DEFAULT_MESSAGES[ErrorCode.INTERNAL_ERROR.value])
    candidate = fallback if message is None or str(message).strip() == "" else str(message)
    candidate = candidate.replace("\r", " ").replace("\n", " ").strip()
    if len(candidate) > 300:
        candidate = candidate[:297].rstrip() + "..."
    if contains_forbidden_detail(candidate):
        candidate = fallback
    return {"code": value, "message": candidate}


def safe_message(message: str | None, code: Any) -> str:
    """Return a client-safe message for ``code`` (never internal detail)."""

    return error_payload(code, message)["message"]


class AppError(Exception):
    """Base class for every domain failure that maps onto the envelope."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_message: str = DEFAULT_MESSAGES[ErrorCode.INTERNAL_ERROR.value]

    def __init__(
        self,
        message: str | None = None,
        *,
        code: ErrorCode | None = None,
    ) -> None:
        self.code = code or type(self).code
        self.message = safe_message(message or type(self).default_message, self.code)
        super().__init__(self.message)

    @property
    def status_code(self) -> int:
        return status_for(self.code)

    def to_payload(self) -> dict[str, dict[str, str]]:
        return error_payload(self.code, self.message)


class StorageUnavailableError(AppError):
    """The SQLite task store is missing, unwritable or otherwise unusable."""

    code = ErrorCode.STORAGE_UNAVAILABLE
    default_message = DEFAULT_MESSAGES[ErrorCode.STORAGE_UNAVAILABLE.value]


class ValidationFailed(AppError):
    """The request payload failed a domain or schema rule."""

    code = ErrorCode.VALIDATION_ERROR
    default_message = DEFAULT_MESSAGES[ErrorCode.VALIDATION_ERROR.value]


class ResourceNotFound(AppError):
    """The addressed route or resource does not exist."""

    code = ErrorCode.NOT_FOUND
    default_message = DEFAULT_MESSAGES[ErrorCode.NOT_FOUND.value]
