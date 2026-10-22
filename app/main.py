from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api import (
    create_task,
    delete_task,
    get_health,
    get_task,
    list_tasks,
    update_task,
)
from app.config import config
from app.error_contract import install_error_contract
from app.storage import get_store


def options_tasks(request: Request):
    return Response(status_code=204, headers={"cache-control": "no-store"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.state.store = get_store()
    app.state.store.count_tasks()

    def setup_routes():
        routes = [
            ("/health", get_health, ["GET"], "health"),
            ("/tasks", list_tasks, ["GET"], "list_tasks"),
            ("/tasks", create_task, ["POST"], "create_task"),
            ("/tasks/{task_id}", get_task, ["GET"], "get_task"),
            ("/tasks/{task_id}", update_task, ["PATCH"], "update_task"),
            ("/tasks/{task_id}", delete_task, ["DELETE"], "delete_task"),
            ("/tasks", options_tasks, ["OPTIONS"], "options_tasks"),
        ]
        for path, handler, methods, name in routes:
            app.add_api_route(path, handler, methods=methods, name=name, response_model=None)

    def setup_middleware():
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.cors.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["*"],
        )

    def setup_exceptions():
        @app.exception_handler(Exception)
        async def generic_exception_handler(request, exc):
            return JSONResponse(
                status_code=500,
                content={"code": "internal_error", "message": "Internal server error"},
                headers={"cache-control": "no-store"},
            )

    setup_routes()
    setup_middleware()
    setup_exceptions()
    install_error_contract(app)
    return app


app = create_app()


def run():
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=config.store.port,
        reload=False,
        log_level="warning",
    )


if __name__ == "__main__":
    run()
