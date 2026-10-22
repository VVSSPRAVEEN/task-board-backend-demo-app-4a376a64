"""Readiness contract: storage probe plus task count, one flat error shape."""

from __future__ import annotations

from starlette.responses import JSONResponse

from app import storage_guard
from app.storage import get_store


def get_health() -> JSONResponse:
    store = get_store()
    probe = storage_guard.probe_store(store)
    if not probe.ok:
        return JSONResponse(
            status_code=503,
            content={
                "code": "storage_unavailable",
                "message": "The task store is temporarily unavailable.",
            },
            headers={"cache-control": "no-store"},
        )
    try:
        count = store.count_tasks()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "code": "storage_unavailable",
                "message": "The task store is temporarily unavailable.",
            },
            headers={"cache-control": "no-store"},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "task_count": count},
        headers={"cache-control": "no-store"},
    )
