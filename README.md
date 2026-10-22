# Task Board Backend Demo

Minimal backend-only HTTP API storing tasks for the Task Board Frontend Demo, runnable and testable independently with SQLite storage.

## Requirements

- Python 3.11+
- `uv`, `pip`, or any Python package manager
- `pytest`

## Install

```bash
pip install -r requirements.txt
```

## Start

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Or with a custom database path:

```bash
DB_PATH=/data/tasks.db uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Test

```bash
pytest tests/
```

## Acceptance checks (live)

The live acceptance suite runs against a started service. Start the service, then:

```bash
P3_ACCEPTANCE_BASE_URL=http://127.0.0.1:8001 pytest tests/test_acceptance_live.py -v
```

## curl examples per endpoint

**GET /health**

```bash
curl -s http://127.0.0.1:8001/health
```

Expected: `200` with `{"status": "ok", "task_count": 0}`.

**GET /tasks**

```bash
curl -s http://127.0.0.1:8001/tasks
```

Expected: `200` with an array of task objects.

**POST /tasks**

```bash
curl -s -X POST http://127.0.0.1:8001/tasks -H "Content-Type: application/json" -d '{"title": "My task", "description": "Do this", "status": "todo"}'
```

Expected: `201` with `{"id": "<uuid>", "title": "My task", "description": "Do this", "status": "todo"}`.

**GET /tasks/{id}**

```bash
curl -s http://127.0.0.1:8001/tasks/<id>
```

Expected: `200` with the task object, or `404` if not found.

**PATCH /tasks/{id}**

```bash
curl -s -X PATCH http://127.0.0.1:8001/tasks/<id> -H "Content-Type: application/json" -d '{"status": "done"}'
```

Expected: `200` with the updated task object.

**DELETE /tasks/{id}**

```bash
curl -s -X DELETE http://127.0.0.1:8001/tasks/<id>
```

Expected: `204` with no body, or `404` if not found.

**OPTIONS /tasks (CORS preflight)**

```bash
curl -s -X OPTIONS http://127.0.0.1:8001/tasks -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type"
```

Expected: `204` with `Access-Control-Allow-Origin: http://localhost:5173` and `Access-Control-Allow-Methods: GET, POST, PATCH, DELETE`.

## Configuration

- `PORT` - listening port (default: `8001`).
- `DB_PATH` - SQLite database file path (default: `/tmp/task-board.db`). Use `/data/tasks.db` or another writable persistent path for container deployments.
- `MAX_BODY_BYTES` - maximum request body size in bytes (default: `65536`).
- `P3_DATA_DIR` - documented writable persistent path hint for container deployments.

## CORS

Only `http://localhost:5173` and `http://localhost:4173` are allowed. No credentials, no wildcard origins. OPTIONS preflight is supported for GET, POST, PATCH and DELETE.

## Docker

```bash
docker compose up --build
```

## Test matrix

Run all unit and integration tests:

```bash
pytest tests/ -v
```

Run acceptance checks against a live service:

```bash
P3_ACCEPTANCE_BASE_URL=http://127.0.0.1:8001 pytest tests/test_acceptance_live.py -v
```

## Runtime contract

The service is a Python FastAPI application at `.`. Tests are authored with pytest against the actual routes and services. The suite is hermetic and CI-stable: every test controls its own environment variables, writes only under `tmp_path`, and works in a read-only container filesystem as a non-root user.