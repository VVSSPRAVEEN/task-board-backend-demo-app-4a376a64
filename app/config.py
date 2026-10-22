from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class StoreConfig:
    database_path: str = field(
        default_factory=lambda: os.environ.get("DB_PATH", "/tmp/task-board.db")
    )
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8001")))
    max_body_bytes: int = field(
        default_factory=lambda: int(os.environ.get("MAX_BODY_BYTES", "65536"))
    )
    writable_path: str = field(default_factory=lambda: os.environ.get("P3_DATA_DIR", "/data"))
    allowed_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:4173"]
    )


@dataclass
class CORSConfig:
    allowed_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:4173"]
    )
    credentials: bool = False
    preflight_methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PATCH", "DELETE"])


@dataclass
class Config:
    store: StoreConfig = field(default_factory=StoreConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)

    @property
    def allowed_origins(self) -> list[str]:
        return self.cors.allowed_origins

    @property
    def credentials(self) -> bool:
        return self.cors.credentials


config = Config()
