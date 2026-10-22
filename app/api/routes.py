from __future__ import annotations

import sqlite3

from starlette.requests import Request  # noqa: TC002
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.api.errors import error_response
from app.validation import (
    validate_task_create_payload,
    validate_task_patch_payload,
)

_NO_STORE = {"cache-control": "no-store"}


def _unavailable() -> JSONResponse:
    return error_response("storage_unavailable", "The task store is temporarily unavailable.", 503)


async def create_task(request: Request) -> JSONResponse:
    payload = await request.json()
    errors = validate_task_create_payload(payload)
    if errors:
        return error_response("validation_error", errors[0].message, 422)
    store = request.app.state.store
    try:
        task = store.add_task(
            payload["title"].strip(),
            (payload.get("description") or "").strip(),
            payload.get("status") or "todo",
        )
    except sqlite3.Error:
        return _unavailable()
    return JSONResponse(status_code=HTTP_201_CREATED, content=task, headers=_NO_STORE)


async def list_tasks(request: Request) -> JSONResponse:
    store = request.app.state.store
    try:
        tasks = store.list_tasks()
    except sqlite3.Error:
        return _unavailable()
    return JSONResponse(content=tasks, headers=_NO_STORE)


async def get_task(request: Request, task_id: str) -> Response | JSONResponse:
    store = request.app.state.store
    try:
        task = store.get_task(task_id)
    except sqlite3.Error:
        return _unavailable()
    if task is None:
        return error_response("not_found", f"Task {task_id} not found", 404)
    return JSONResponse(content=task, headers=_NO_STORE)


async def update_task(request: Request, task_id: str) -> Response | JSONResponse:
    payload = await request.json()
    errors = validate_task_patch_payload(payload)
    if errors:
        return error_response("validation_error", errors[0].message, 422)
    store = request.app.state.store
    changes = {
        name: (payload[name].strip() if name == "title" else payload[name])
        for name in ("title", "description", "status")
        if name in payload
    }
    try:
        task = store.update_task(task_id, changes)
    except sqlite3.Error:
        return _unavailable()
    if task is None:
        return error_response("not_found", f"Task {task_id} not found", 404)
    return JSONResponse(content=task, headers=_NO_STORE)


async def delete_task(request: Request, task_id: str) -> Response:
    store = request.app.state.store
    try:
        removed = store.delete_task(task_id)
    except sqlite3.Error:
        return _unavailable()
    if not removed:
        return error_response("not_found", f"Task {task_id} not found", 404)
    return Response(status_code=HTTP_204_NO_CONTENT, headers=_NO_STORE)
