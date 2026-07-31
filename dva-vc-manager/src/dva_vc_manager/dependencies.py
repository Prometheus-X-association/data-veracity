"""FastAPI dependency providers for the DVA VC Manager."""

from __future__ import annotations

import asyncpg
from fastapi import Request

from .config import cfg
from .log import get_logger
from .whitelist import FakeWhitelist, PgWhitelist, WhitelistRepo

logger = get_logger()


async def build_whitelist() -> WhitelistRepo:
    """
    Construct the whitelist repo from config. Called once, at startup.

    With no DSN configured this falls back to the in-memory repo so the
    service still boots for local development.
    """
    if not cfg.postgres_dsn:
        logger.warning(
            "DVA_VC_MANAGER_DB_URL is not set, falling back to in-memory "
            "FakeWhitelist; the whitelist will not survive a restart"
        )
        return FakeWhitelist()

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgWhitelist(pool)
    await repo.ensure_schema()
    return repo


def get_whitelist(request: Request) -> WhitelistRepo:
    """Return the whitelist repo built during startup."""
    return request.app.state.whitelist
