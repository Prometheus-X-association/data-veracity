"""FastAPI application factory and CLI entrypoint.

The application is wired so the repository implementation is resolved
through FastAPI's dependency-injection system. In production the
async-backed ``PgVLARepo`` is constructed on startup (via the lazy
``dependencies.get_repo``); in tests the caller swaps it via
``app.dependency_overrides[get_repo]``.
"""

from __future__ import annotations

from typing import Any

import asyncpg
import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .config import cfg
from .log import get_logger, setup_logging
from .repo import PgTemplateRepo, PgVLARepo
from .routes import router
from .template_routes import router as template_router

logger = get_logger()


def _load_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Return the hand-written spec, or FastAPI's generated one if absent."""
    try:
        with open(cfg.openapi_file, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        logger.warning(
            "OpenAPI spec not found, falling back to the auto-generated schema; "
            "set VLA_MANAGER_OPENAPI_FILE to the hand-written spec",
            openapi_file=cfg.openapi_file,
        )
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )


async def _build_production_repo():
    """Construct the async-backed repository.

    Requires ``cfg.postgres_dsn`` to be set (env ``VLA_MANAGER_DB_URL``).
    Must be awaited from within the running event loop (e.g. the
    ``get_repo`` dependency) — never wrapped in ``asyncio.run()``, which
    raises ``RuntimeError`` when a loop is already running.
    """
    if not cfg.postgres_dsn:
        raise RuntimeError(
            "VLA_MANAGER_DB_URL is not set — cannot boot PgVLARepo. "
            "Either set it or override the get_repo dependency for tests."
        )

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgVLARepo(pool)
    await repo._ensure_schema()
    return repo


async def _build_production_template_repo():
    """Construct the async-backed Template repository.

    Opens its own asyncpg pool against the same database as the VLA repo,
    and owns the separate ``templates`` + ``evaluation_methods`` tables.
    """
    if not cfg.postgres_dsn:
        raise RuntimeError(
            "VLA_MANAGER_DB_URL is not set — cannot boot PgTemplateRepo. "
            "Either set it or override the get_template_repo dependency for tests."
        )

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgTemplateRepo(pool)
    await repo._ensure_schema()
    return repo


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="VLA Manager API",
        description=(
            "Sole owner of Veracity Level Agreements, hosted at the Data "
            "Intermediary. Serves ``GET /vla/{id}`` to each participant's "
            "DVA API during attestation (steps 2-3 of the synchronous flow) "
            "and serves the VLA authoring UI for VLA CRUD."
        ),
        version="0.1.0",
        # Docs pages are FastAPI's own; the schema behind them is the
        # hand-written spec assigned below.
        docs_url="/swagger",
        redoc_url="/redoc",
        openapi_url="/swagger/openapi.json",
    )
    app.include_router(router)
    app.include_router(template_router)
    # Populating openapi_schema is what app.openapi() consults first, so
    # Swagger UI and ReDoc both render the hand-written spec.
    app.openapi_schema = _load_openapi_schema(app)

    return app


# Module-level app — used by ``uvicorn vla_manager_api.main:app`` and by
# the ``TestClient`` in ``tests/test_vla_crud.py``.
app = create_app()


def cli() -> None:
    """uvicorn entrypoint (see ``[project.scripts]`` in pyproject.toml)."""
    uvicorn.run(
        "vla_manager_api.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level,
    )
