"""Canonical HTTP error contract installed by the repair skill layer."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

if TYPE_CHECKING:
    from fastapi import FastAPI, Request


MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", "65536"))
_WRITE_METHODS = {"POST", "PUT", "PATCH"}


def _envelope(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def _flat(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def install_error_contract(app: FastAPI) -> None:
    """Install one envelope, one body guard and one set of status mappings."""
    if getattr(app.state, "error_contract_installed", False):
        return
    app.state.error_contract_installed = True

    @app.middleware("http")
    async def _request_guard(request: Request, call_next):
        if request.method.upper() in _WRITE_METHODS:
            media = request.headers.get("content-type", "").split(";")[0].strip().lower()
            if media != "application/json":
                return JSONResponse(
                    status_code=415,
                    content=_flat(
                        "unsupported_media_type",
                        "Content-Type must be application/json.",
                    ),
                )
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content=_flat(
                        "payload_too_large",
                        "Request body exceeds the maximum allowed size.",
                    ),
                )

        return await call_next(request)

    @app.exception_handler(json.JSONDecodeError)
    async def _invalid_json(request: Request, exc: json.JSONDecodeError):
        return JSONResponse(
            status_code=400,
            content=_flat("invalid_json", "Request body must be valid JSON."),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if any(str(item.get("type") or "") == "json_invalid" for item in errors):
            return JSONResponse(
                status_code=400,
                content=_flat("invalid_json", "Request body must be valid JSON."),
            )
        return JSONResponse(
            status_code=422,
            content=_flat("validation_error", "The request payload failed validation."),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = "not_found" if exc.status_code == 404 else "internal_error"
        message = (
            "The requested resource does not exist."
            if code == "not_found"
            else "An unexpected internal error occurred."
        )
        return JSONResponse(status_code=exc.status_code, content=_flat(code, message))
