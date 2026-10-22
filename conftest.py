"""Root conftest: make the repository root importable before any collection.

The service is started as `uvicorn app.main:app` from the repository root and the
acceptance runner executes with the same working directory, but pytest is also
invoked from subdirectories (and from tox environments whose cwd differs).  The
suites import `app.config`, `app.main` and friends by package name, so the
repository root must be on `sys.path` for those imports to resolve without an
editable install.  Doing it here, in a root-level conftest, guarantees the path
is in place before pytest imports any test module or plugin that touches the
package.

`tests/conftest.py` owns the fixtures (temporary DB_PATH, TestClient, live
service); this file deliberately owns nothing else, so there is exactly one
place that mutates import state and one place that defines fixtures.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def _ensure_repo_root_on_sys_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_repo_root_on_sys_path()
