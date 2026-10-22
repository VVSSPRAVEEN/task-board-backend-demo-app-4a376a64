"""Request models and field rules for the Task Board API.

The models are the single definition of the write contract: Pydantic rejects
unknown fields, wrong JSON types and out-of-range values before a route runs.
Trimming happens before the length checks so a whitespace-only title cannot
sneak past ``min_length``.

``TaskUpdate`` distinguishes "field omitted" from "field supplied as null".
Omitted means unchanged; an explicit null is rejected, because every writable
field is a string in the public contract.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

MIN_TITLE = 1
MAX_TITLE = 80
MIN_DESCRIPTION = 0
MAX_DESCRIPTION = 280

STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_VALUES = (STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE)

_TITLE_MESSAGE = f"title must be between {MIN_TITLE} and {MAX_TITLE} characters"
_DESCRIPTION_MESSAGE = f"description must be at most {MAX_DESCRIPTION} characters"
_STATUS_MESSAGE = f"status must be one of {STATUS_VALUES}"


def _clean_title(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) < MIN_TITLE or len(trimmed) > MAX_TITLE:
        raise ValueError(_TITLE_MESSAGE)
    return trimmed


def _clean_description(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) > MAX_DESCRIPTION:
        raise ValueError(_DESCRIPTION_MESSAGE)
    return trimmed


def _clean_status(value: str) -> str:
    if value not in STATUS_VALUES:
        raise ValueError(_STATUS_MESSAGE)
    return value


class TaskCreate(BaseModel):
    """Body of ``POST /api/tasks``."""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    status: str = STATUS_TODO

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _clean_title(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        return _clean_description(value)

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        return _clean_status(value)


class TaskUpdate(BaseModel):
    """Body of ``PATCH /api/tasks/{id}``.

    At least one writable field must be supplied, and no supplied field may be
    null.  ``model_fields_set`` is what makes that distinction possible: Pydantic
    fills omitted optional fields with ``None`` exactly like an explicit null.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    status: str | None = None

    @field_validator("title")
    @classmethod
    def _title(cls, value: str | None) -> str | None:
        return None if value is None else _clean_title(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str | None) -> str | None:
        return None if value is None else _clean_description(value)

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        return None if value is None else _clean_status(value)

    @model_validator(mode="after")
    def _require_supplied_values(self) -> TaskUpdate:
        supplied = self.model_fields_set
        if not supplied:
            raise ValueError("at least one of title, description or status is required")
        nulls = sorted(name for name in supplied if getattr(self, name, None) is None)
        if nulls:
            raise ValueError(f"field(s) may not be null: {', '.join(nulls)}")
        return self

    def changes(self) -> dict[str, Any]:
        """Return only the fields the client actually supplied."""
        return {
            name: getattr(self, name)
            for name in self.model_fields_set
            if name in {"title", "description", "status"}
        }
