from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime

from app.config import config

_DBConnection = sqlite3.Connection


class TaskStore:
    """Parameterized SQLite access with non-destructive table creation and atomic transactions."""

    SCHEMA_VERSION = 2

    def __init__(self, db_path: str | None = None) -> None:
        self._path = db_path or os.environ.get("DB_PATH") or config.store.database_path
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None
        self._opened = False
        with self._connection():
            pass

    @contextmanager
    def _connection(self):
        if self._conn is None:
            with self._lock:
                if self._conn is None:
                    os.makedirs(os.path.dirname(self._path), exist_ok=True)
                    self._conn = sqlite3.connect(self._path, check_same_thread=False)
                    self._conn.row_factory = sqlite3.Row
                    self._ensure_table()
        yield self._conn

    def connection(self):
        return self._connection()

    def _ensure_table(self) -> None:
        cursor = self._conn.cursor()
        version = cursor.execute("PRAGMA user_version").fetchone()[0]
        if version < self.SCHEMA_VERSION:
            self._migrate(cursor, version)
            self._conn.execute("PRAGMA user_version = 2")

            self._conn.commit()

    def _migrate(self, cursor: sqlite3.Cursor, from_version: int) -> None:
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(tasks)").fetchall()]
        if "done" in columns and "status" not in columns:
            cursor.execute("ALTER TABLE tasks RENAME TO legacy_tasks")
            cursor.execute("""
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'todo',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO tasks (id, title, description, status, created_at)
                SELECT CAST(id AS TEXT), title, '',
                       CASE done WHEN 1 THEN 'done' ELSE 'todo' END, created_at
                FROM legacy_tasks
            """)
            cursor.execute("DROP TABLE legacy_tasks")
            return
        if from_version == 0:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'todo',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            legacy = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legacy_tasks'"
            ).fetchone()
            if legacy:
                cursor.execute("""
                    INSERT INTO tasks (id, title, description, status, created_at)
                    SELECT CAST(id AS TEXT), title, description,
                           CASE done WHEN 1 THEN 'done' ELSE 'todo' END, created_at
                    FROM legacy_tasks
                """)
                cursor.execute("DROP TABLE legacy_tasks")
        elif from_version == 1:
            cursor.execute("""
                ALTER TABLE tasks ADD COLUMN description TEXT
            """)

    def init_schema(self) -> int:
        with self._connection() as conn:
            return conn.execute("PRAGMA user_version").fetchone()[0]

    def add_task(self, title: str, description: str | None = None, status: str = "todo") -> dict:
        import uuid

        tid = str(uuid.uuid4())
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO tasks (id, title, description, status, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (tid, title, description, status, datetime.now(UTC).isoformat()),
            )
            conn.commit()
        return self.get_task(tid)

    def list_tasks(self) -> list[dict]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, title, description, status, created_at FROM tasks ORDER BY rowid"
            ).fetchall()
            return [self._row_to_task(r) for r in rows]

    def get_task(self, tid: str) -> dict | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
                (tid,),
            ).fetchone()
            return self._row_to_task(row) if row is not None else None

    def update_task(self, tid: str, updates: dict) -> dict | None:
        with self._connection() as conn:
            if self.get_task(tid) is None:
                return None
            if not any(key in updates for key in ("title", "description", "status")):
                return self.get_task(tid)
            conn.execute(
                "UPDATE tasks SET "
                "title = CASE WHEN ? THEN ? ELSE title END, "
                "description = CASE WHEN ? THEN ? ELSE description END, "
                "status = CASE WHEN ? THEN ? ELSE status END "
                "WHERE id = ?",
                (
                    "title" in updates,
                    updates.get("title"),
                    "description" in updates,
                    updates.get("description"),
                    "status" in updates,
                    updates.get("status"),
                    tid,
                ),
            )
            conn.commit()

        return self.get_task(tid)

    def delete_task(self, tid: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (tid,))
            conn.commit()
            return cur.rowcount > 0

    def count_tasks(self) -> int:
        with self._connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    def _row_to_task(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "status": row["status"],
            "created_at": row["created_at"],
        }

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


_STORE: TaskStore | None = None


def get_store() -> TaskStore:
    """Return the process-wide task store used by the API layer."""
    global _STORE
    if _STORE is None:
        _STORE = TaskStore()
    return _STORE


def reset_store() -> None:
    global _STORE
    if _STORE is not None:
        try:
            _STORE.close()
        finally:
            _STORE = None
