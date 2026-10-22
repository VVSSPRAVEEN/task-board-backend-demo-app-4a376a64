from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationError:
    field: str
    message: str


def validate_title(value: Any) -> ValidationError | None:
    if value is None:
        return ValidationError("title", "title is required")
    if not isinstance(value, str):
        return ValidationError("title", "title must be a string")
    if value.strip() == "":
        return ValidationError("title", "title must not be empty or whitespace-only")
    if len(value) > 80:
        return ValidationError("title", "title must not exceed 80 characters")
    return None


def validate_description(value: Any) -> ValidationError | None:
    if value is None:
        return ValidationError("description", "description must be a string")

    if not isinstance(value, str):
        return ValidationError("description", "description must be a string")
    if len(value) > 280:
        return ValidationError("description", "description must not exceed 280 characters")
    return None


def validate_status(value: Any) -> ValidationError | None:
    if value is None:
        return ValidationError("status", "status must be a string")

    if not isinstance(value, str):
        return ValidationError("status", "status must be a string")
    if value not in ("todo", "in_progress", "done"):
        return ValidationError("status", "status must be one of: todo, in_progress, done")
    return None


def validate_task_create_payload(payload: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if "title" not in payload:
        errors.append(ValidationError("title", "title is required"))
    else:
        err = validate_title(payload["title"])
        if err:
            errors.append(err)
    if "description" in payload:
        err = validate_description(payload["description"])
        if err:
            errors.append(err)
    if "status" in payload:
        err = validate_status(payload["status"])
        if err:
            errors.append(err)
    if "id" in payload:
        errors.append(ValidationError("id", "client-supplied ids are not allowed"))
    known = {"title", "description", "status"}
    for key in payload:
        if key not in known:
            errors.append(ValidationError(key, "unknown field"))
    return errors


def validate_task_patch_payload(payload: dict[str, Any]) -> list[ValidationError]:
    if not isinstance(payload, dict) or len(payload) == 0:
        return [ValidationError("body", "PATCH body must contain at least one updatable field")]
    errors: list[ValidationError] = []
    if "id" in payload:
        errors.append(ValidationError("id", "client-supplied ids are not allowed"))
    known = {"title", "description", "status"}
    for key in payload:
        if key not in known:
            errors.append(ValidationError(key, "unknown field"))
    if "title" in payload:
        err = validate_title(payload["title"])
        if err:
            errors.append(err)
    if "description" in payload:
        err = validate_description(payload["description"])
        if err:
            errors.append(err)
    if "status" in payload:
        err = validate_status(payload["status"])
        if err:
            errors.append(err)
    return errors
