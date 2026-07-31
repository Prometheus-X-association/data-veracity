"""FastAPI application factory and CLI entrypoint for the DVA VC Manager."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .config import cfg
from .dependencies import build_key_store, build_whitelist
from .log import get_logger, setup_logging
from .routes import admin_router, router

logger = get_logger()


def _spec_loader(app: FastAPI) -> Callable[[], dict[str, Any]]:
    """
    Build the ``app.openapi`` callable serving the hand-written spec.

    FastAPI caches the result in ``app.openapi_schema`` and renders both the
    Swagger UI and ReDoc pages from it, so the spec is read from disk once.
    """

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        try:
            with open(cfg.openapi_file, "r", encoding="utf-8") as fh:
                app.openapi_schema = yaml.safe_load(fh)
        except FileNotFoundError:
            logger.warning(
                "OpenAPI spec not found, falling back to the auto-generated schema; "
                "set DVA_VC_MANAGER_OPENAPI_FILE to the hand-written spec",
                openapi_file=cfg.openapi_file,
            )
            app.openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
        return app.openapi_schema

    return openapi


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the whitelist repo (and its connection pool) up front."""
    app.state.key_store = build_key_store()
    app.state.whitelist = await build_whitelist()
    try:
        yield
    finally:
        await app.state.whitelist.close()


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        lifespan=lifespan,
        title="DVA VC Manager",
        description=(
            "Issues and verifies Attestation of Veracity (AoV) credentials as "
            "W3C VC 2.0 JSON-LD JWS (Ed25519) using PyNaCl. Hosted at "
            "each Participant. Called by the DVA API during credential "
            "issuance in the synchronous attestation flow."
        ),
        version="0.1.0",
        # Docs pages are FastAPI's own; the schema behind them is the
        # hand-written spec installed as app.openapi below.
        docs_url="/swagger",
        redoc_url="/redoc",
        openapi_url="/swagger/openapi.json",
    )
    app.include_router(router)
    app.include_router(admin_router)
    app.openapi = _spec_loader(app)

    return app


app = create_app()


def cli() -> None:
    uvicorn.run(
        "dva_vc_manager.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level,
    )
