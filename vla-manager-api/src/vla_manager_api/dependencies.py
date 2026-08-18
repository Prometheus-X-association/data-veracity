"""FastAPI dependency providers.

Kept separate from :mod:`.main` and :mod:`.routes` to avoid circular
imports — :mod:`.main` imports :mod:`.routes` which imports
:mod:`.dependencies`. Tests override providers via
``app.dependency_overrides``.
"""

from __future__ import annotations

from .config import cfg
from .log import get_logger
from .repo import FakeTemplateRepo, FakeVLARepo, TemplateRepo, VLARepo

logger = get_logger()

# Lazy singleton — populated on first request. Tests override via
# ``app.dependency_overrides[get_repo] = lambda: FakeVLARepo()``.
_repo_singleton: VLARepo | None = None


async def get_repo() -> VLARepo:
    global _repo_singleton
    if _repo_singleton is None:
        if cfg.postgres_dsn:
            from .main import _build_production_repo

            _repo_singleton = await _build_production_repo()
        else:
            # Dev convenience: boot with an in-memory repo so a bare
            # ``uvicorn vla_manager_api.main:app`` works without a
            # Postgres. State is lost on restart, so do NOT use this
            # mode in production — set VLA_MANAGER_DB_URL.
            logger.warning(
                "VLA_MANAGER_DB_URL is not set — falling back to FakeVLARepo "
                "(in-memory). State will be lost on restart. Configure "
                "VLA_MANAGER_DB_URL for production use."
            )
            _repo_singleton = FakeVLARepo()
    return _repo_singleton


# --- Template repo (same lazy-singleton pattern) ---
_template_repo_singleton: TemplateRepo | None = None


async def get_template_repo() -> TemplateRepo:
    global _template_repo_singleton
    if _template_repo_singleton is None:
        if cfg.postgres_dsn:
            from .main import _build_production_template_repo

            _template_repo_singleton = await _build_production_template_repo()
        else:
            logger.warning(
                "VLA_MANAGER_DB_URL is not set — falling back to FakeTemplateRepo "
                "(in-memory). State will be lost on restart."
            )
            _template_repo_singleton = FakeTemplateRepo()
    return _template_repo_singleton
