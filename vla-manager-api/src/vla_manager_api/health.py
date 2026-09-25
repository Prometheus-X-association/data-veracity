"""
Health endpoints; see ``docs/health-checks.md``.

* ``GET /livez`` – ``pass`` as long as the process serves HTTP.
* ``GET /readyz`` – ``fail`` when Postgres does not answer, ``warn`` when
  none is configured (VLAs and templates are then kept in memory).

Both answer ``{"status": ..., "output": ...}``, ``output`` giving the reason
when the status is not ``pass``, with 503 on ``fail``.
"""

from __future__ import annotations

import asyncio
from typing import Literal, Optional

import asyncpg
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .config import cfg

TIMEOUT_SECONDS = 2.0

router = APIRouter(tags=["Health"])


def _health(
    status: Literal["pass", "warn", "fail"], output: Optional[str] = None
) -> JSONResponse:
    body = (
        {"status": status} if output is None else {"status": status, "output": output}
    )
    return JSONResponse(
        body,
        status_code=503 if status == "fail" else 200,
        media_type="application/health+json",
    )


async def _ping_postgres(dsn: str) -> None:
    conn = await asyncpg.connect(dsn, timeout=TIMEOUT_SECONDS)
    try:
        await conn.fetchval("SELECT 1")
    finally:
        await conn.close()


@router.get("/livez")
async def livez() -> JSONResponse:
    return _health("pass")


@router.get("/readyz")
async def readyz() -> JSONResponse:
    if not cfg.postgres_dsn:
        return _health("warn", "VLA_MANAGER_DB_URL is not set; data is kept in memory")
    try:
        await asyncio.wait_for(_ping_postgres(cfg.postgres_dsn), TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return _health("fail", "postgres: timed out")
    except Exception as e:
        return _health("fail", f"postgres: {str(e) or type(e).__name__}")
    return _health("pass")
