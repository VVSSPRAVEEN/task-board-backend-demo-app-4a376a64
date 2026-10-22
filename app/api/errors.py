from __future__ import annotations

from starlette.responses import JSONResponse


def error_response(code: str, message: str, status: int = 422) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message},
        headers={"cache-control": "no-store"},
    )
