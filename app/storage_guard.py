from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage import _DBConnection


@dataclass
class StorageProbeResult:
    ok: bool
    reason: str | None = None

    @classmethod
    def healthy(cls) -> StorageProbeResult:
        return cls(ok=True)

    @classmethod
    def unhealthy(cls, reason: str) -> StorageProbeResult:
        return cls(ok=False, reason=reason)


def probe_store(store: _DBConnection) -> StorageProbeResult:
    try:
        with store.connection() as conn:
            conn.execute("SELECT 1")
        return StorageProbeResult.healthy()
    except Exception:
        return StorageProbeResult.unhealthy("storage_unreachable")
