"""Compatibility import for the service's task store.

The service uses :class:`app.storage.TaskStore`; this module keeps the historical
import path working for the acceptance and integration suites.
"""

from app.storage import TaskStore, get_store, reset_store

SCHEMA_VERSION = 2

__all__ = ["SCHEMA_VERSION", "TaskStore", "get_store", "reset_store"]
