"""Runtime configuration for the VLA Manager API.

Read from environment variables (mirrors dva-processing's config style —
plain module-level constants instead of a config dataclass, so the rest
of the codebase can ``from .config import cfg``).
"""

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
    host: str = os.getenv("VLA_MANAGER_API_HOST", "0.0.0.0")
    port: int = int(os.getenv("VLA_MANAGER_API_PORT", "8000"))
    log_level: int = _log_level(os.getenv("VLA_MANAGER_API_LOG_LEVEL", "INFO"))

    # Postgres DSN. Required for the production (asyncpg) repository.
    # Example: postgresql://vla:vla@postgres-vla:5432/vla
    postgres_dsn: str = os.getenv("VLA_MANAGER_DB_URL", "")

    # Hand-written OpenAPI spec served at /swagger.
    # Missing → fall back to FastAPI's auto-generated schema.
    openapi_file: str = os.getenv("VLA_MANAGER_OPENAPI_FILE", "/app/openapi.yaml")


cfg = Config()


def setup_logging() -> None:
    shared = [add_log_level, StackInfoRenderer(), TimeStamper(fmt="iso")]
    processors = shared + ([ConsoleRenderer()] if stderr.isatty() else [JSONRenderer()])
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(cfg.log_level),
    )
