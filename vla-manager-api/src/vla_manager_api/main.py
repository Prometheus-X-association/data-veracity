"""
FastAPI application factory and CLI entrypoint.

The application is wired so the repository implementations are resolved
through FastAPI's dependency-injection system. In production both repos
are built once during ``lifespan`` and read off ``app.state``; in tests
the caller swaps them via ``app.dependency_overrides[get_repo]``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import cfg
from .dependencies import build_pool, build_template_repo, build_vla_repo
from .errors import http_exception_handler
from .log import get_logger, setup_logging
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build both repositories up front and close the pool on shutdown."""
    app.state.pool = await build_pool()
    app.state.vla_repo = await build_vla_repo(app.state.pool)
    app.state.template_repo = await build_template_repo(app.state.pool)
    try:
        yield
    finally:
        if app.state.pool is not None:
            await app.state.pool.close()


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        lifespan=lifespan,
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
    # Render errors as the spec's {type, title} rather than FastAPI's
    # {"detail": ...}. Registered for Starlette's exception class so the
    # 404s and 405s the router itself raises are covered too.
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
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
