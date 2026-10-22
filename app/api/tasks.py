from __future__ import annotations

MAX_TITLE = 80
MAX_DESCRIPTION = 280
VALID_STATUSES = {"todo", "in_progress", "done"}


def validate_title(value) -> str | None:
    if value is None or not isinstance(value, str):
        return "title must be a string"
    trimmed = value.strip()
    if not trimmed:
        return "title cannot be empty"
    if len(trimmed) > MAX_TITLE:
        return "title too long"
    return trimmed


def validate_description(value) -> str | None:
    if value is None:
        return ""
    if not isinstance(value, str):
        return "description must be a string"
    if len(value.strip()) > MAX_DESCRIPTION:
        return "description too long"
    return value.strip()


def validate_status(value) -> str | None:
    if value is None:
        return ""
    if not isinstance(value, str):
        return "status must be a string"
    if value.lower() not in VALID_STATUSES:
        return "status must be one of: todo, in_progress, done"
    return value.lower()


def validate_payload(payload: dict) -> dict | str:
    if not isinstance(payload, dict):
        return "payload must be an object"
    if "id" in payload:
        return "id is not allowed in request body"
    if any(key not in ("title", "description", "status") for key in payload):
        return "unknown field in request"
    errors: dict[str, str] = {}
    if "title" in payload:
        res = validate_title(payload["title"])
        if isinstance(res, str):
            errors["title"] = res
    if "description" in payload:
        res = validate_description(payload["description"])
        if isinstance(res, str):
            errors["description"] = res
    if "status" in payload:
        res = validate_status(payload["status"])
        if isinstance(res, str):
            errors["status"] = res
    if errors:
        return errors
    title = payload.get("title", "").strip()
    return {
        "title": title,
        "description": validate_description(payload.get("description")),
        "status": validate_status(payload.get("status")),
    }


def validate_patch(payload: dict) -> dict | str:
    if not isinstance(payload, dict):
        return "payload must be an object"
    if not payload:
        return "patch body must not be empty"
    if "id" in payload:
        return "id is not allowed in request body"
    if any(key not in ("title", "description", "status") for key in payload):
        return "unknown field in request"
    errors: dict[str, str] = {}
    if "title" in payload:
        res = validate_title(payload["title"])
        if isinstance(res, str):
            errors["title"] = res
    if "description" in payload:
        res = validate_description(payload["description"])
        if isinstance(res, str):
            errors["description"] = res
    if "status" in payload:
        res = validate_status(payload["status"])
        if isinstance(res, str):
            errors["status"] = res
    if errors:
        return errors
    out: dict = {}
    if "title" in payload:
        out["title"] = payload["title"].strip()
    if "description" in payload:
        out["description"] = validate_description(payload["description"])
    if "status" in payload:
        out["status"] = validate_status(payload["status"])
    return out
