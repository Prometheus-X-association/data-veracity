"""Runtime configuration for the DVA VC Manager."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    host: str = os.getenv("DVA_VC_MANAGER_HOST", "0.0.0.0")
    port: int = int(os.getenv("DVA_VC_MANAGER_PORT", "8000"))

    # Level name, lowercased: structlog and uvicorn both take one of
    # "critical", "error", "warning", "info", "debug".
    log_level: str = os.getenv("DVA_VC_MANAGER_LOG_LEVEL", "info").lower()

    # Ed25519 signing key file path.
    # Loaded on first use; created and persisted (0600) if missing.
    signing_key_path: str = os.getenv(
        "DVA_VC_MANAGER_SIGNING_KEY_PATH", "/data/dva-vc-signing-key.pem"
    )

    # Postgres DSN (whitelist).  Required for the production (asyncpg)
    # whitelist repo; empty → fall back to in-memory FakeWhitelist.
    postgres_dsn: str = os.getenv("DVA_VC_MANAGER_DB_URL", "")

    # Hand-written OpenAPI spec served at /swagger.
    # Missing → fall back to FastAPI's auto-generated schema.
    openapi_file: str = os.getenv("DVA_VC_MANAGER_OPENAPI_FILE", "/app/openapi.yaml")


cfg = Config()
