"""FastAPI dependency providers for the VLA Manager API."""

from __future__ import annotations

import asyncpg
from fastapi import Request

from .config import cfg
from .log import get_logger
from .template_repo import FakeTemplateRepo, PgTemplateRepo, TemplateRepo
from .validation import ProcessingRequirementValidator, RequirementValidator
from .vla_repo import FakeVLARepo, PgVLARepo, VLARepo

logger = get_logger()


async def build_pool() -> asyncpg.Pool | None:
    """
    Open the connection pool shared by both repositories.

    With no DSN configured this returns ``None`` so the service still
    boots for local development, backed by the in-memory repos.
    """
    if not cfg.postgres_dsn:
        logger.warning(
            "VLA_MANAGER_DB_URL is not set, falling back to in-memory "
            "repositories; VLAs and templates will not survive a restart"
        )
        return None

    return await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)


async def build_vla_repo(pool: asyncpg.Pool | None) -> VLARepo:
    """Construct the VLA repo over ``pool``. Called once, at startup."""
    if pool is None:
        return FakeVLARepo()

    repo = PgVLARepo(pool)
    await repo.ensure_schema()
    return repo


async def build_template_repo(pool: asyncpg.Pool | None) -> TemplateRepo:
    """
    Construct the Template repo over ``pool``. Called once, at startup.

    Shares the pool with the VLA repo but owns the separate ``templates``
    + ``evaluation_methods`` tables.
    """
    if pool is None:
        return FakeTemplateRepo()

    repo = PgTemplateRepo(pool)
    await repo.ensure_schema()
    return repo


def get_repo(request: Request) -> VLARepo:
    """Return the VLA repo built during startup."""
    return request.app.state.vla_repo


def get_template_repo(request: Request) -> TemplateRepo:
    """Return the Template repo built during startup."""
    return request.app.state.template_repo


def get_requirement_validator() -> RequirementValidator:
    """Return the processing-backed evaluation logic validator."""
    return ProcessingRequirementValidator(cfg.processing_url)
