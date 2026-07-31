"""FastAPI dependency providers for the DVA VC Manager."""

from __future__ import annotations

import logging

from .config import cfg
from .whitelist import FakeWhitelist, WhitelistRepo

logger = logging.getLogger(__name__)

_whitelist_singleton: WhitelistRepo | None = None


async def get_whitelist() -> WhitelistRepo:
    global _whitelist_singleton
    if _whitelist_singleton is None:
        if cfg.postgres_dsn:
            # Deferred: main imports routes, which imports this module, so a
            # top-level import here would be circular.  The real fix is to
            # move the factory out of main -- see the DB lifecycle cleanup.
            from .main import _build_production_whitelist

            _whitelist_singleton = await _build_production_whitelist()
        else:
            logger.warning(
                "DVA_VC_MANAGER_DB_URL is not set – falling back to in-memory FakeWhitelist"
            )
            _whitelist_singleton = FakeWhitelist()
    return _whitelist_singleton
