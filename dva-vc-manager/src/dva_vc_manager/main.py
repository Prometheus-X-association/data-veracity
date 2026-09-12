"""FastAPI application factory and CLI entrypoint for the DVA VC Manager."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse

from .config import cfg
from .dependencies import build_audit, build_key_store, build_whitelist
from .log import get_logger, setup_logging
from .routes import admin_router, router

logger = get_logger()


def _load_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Return the hand-written spec, or FastAPI's generated one if absent."""
    try:
        with open(cfg.openapi_file, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        logger.warning(
            "OpenAPI spec not found, falling back to the auto-generated schema; "
            "set DVA_VC_MANAGER_OPENAPI_FILE to the hand-written spec",
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
    """Build persistence repositories up front and close them on shutdown."""
    app.state.key_store = build_key_store()
    app.state.whitelist = await build_whitelist()
    try:
        app.state.audit = await build_audit()
        yield
    finally:
        await app.state.whitelist.close()
        if hasattr(app.state, "audit"):
            await app.state.audit.close()


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        lifespan=lifespan,
        title="DVA VC Manager",
        description=(
            "Issues and verifies Attestation of Veracity (AoV) credentials as "
            "W3C VC 2.0 JSON-LD JWS (Ed25519). Hosted at "
            "each Participant. Called by the DVA API during credential "
            "issuance in the synchronous attestation flow."
        ),
        version="0.1.0",
        # Docs pages are FastAPI's own; the schema behind them is the
        # hand-written spec assigned below.
        docs_url="/swagger",
        redoc_url="/redoc",
        openapi_url="/swagger/openapi.json",
    )
    app.include_router(router)
    app.include_router(admin_router)

    @app.get("/swagger/components.yaml", include_in_schema=False)
    async def shared_schemas() -> FileResponse:
        """Serve the schemas the spec shares with the other DVA components.

        The spec refers to them as ``./components.yaml#/schemas/...``, which the
        docs page resolves against the URL it loaded the spec from, ie next to
        ``openapi_url``.  Keeping the reference external means the shared
        document stays the single definition rather than being copied in.
        """
        shared = Path(cfg.openapi_file).parent / "components.yaml"
        if not shared.is_file():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No shared schemas available"
            )
        return FileResponse(shared, media_type="application/yaml")

    # Populating openapi_schema is what app.openapi() consults first, so
    # Swagger UI and ReDoc both render the hand-written spec.
    app.openapi_schema = _load_openapi_schema(app)

    return app


app = create_app()


def cli() -> None:
    uvicorn.run(
        "dva_vc_manager.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level,
    )
