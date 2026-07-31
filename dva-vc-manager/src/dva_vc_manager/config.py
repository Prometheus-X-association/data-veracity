"""Runtime configuration for the DVA VC Manager."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from sys import stderr

import structlog
from structlog import make_filtering_bound_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, StackInfoRenderer, TimeStamper
from structlog.stdlib import add_log_level


def _log_level(value: str | None) -> int:
    return getattr(logging, (value or "INFO").upper(), logging.INFO)


@dataclass
class Config:
    host: str = os.getenv("DVA_VC_MANAGER_HOST", "0.0.0.0")
    port: int = int(os.getenv("DVA_VC_MANAGER_PORT", "8000"))
    log_level: int = _log_level(os.getenv("DVA_VC_MANAGER_LOG_LEVEL", "INFO"))

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


def setup_logging() -> None:
    shared = [add_log_level, StackInfoRenderer(), TimeStamper(fmt="iso")]
    processors = shared + ([ConsoleRenderer()] if stderr.isatty() else [JSONRenderer()])
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(cfg.log_level),
    )
