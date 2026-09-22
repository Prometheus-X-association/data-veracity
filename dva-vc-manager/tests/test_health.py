"""Tests for ``GET /livez`` and ``GET /readyz``; Postgres is stubbed out."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from dva_vc_manager import health
from dva_vc_manager.config import cfg
from dva_vc_manager.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def with_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cfg, "postgres_dsn", "postgresql://db/dva")


def _pinging(monkeypatch: pytest.MonkeyPatch, ping) -> None:
    monkeypatch.setattr(health, "_ping_postgres", ping)


async def _ok(_: str) -> None:
    return None


async def _refused(_: str) -> None:
    raise ConnectionRefusedError("connection refused")


def test_livez_passes(client: TestClient) -> None:
    r = client.get("/livez")

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/health+json"
    assert r.json() == {"status": "pass"}


@pytest.mark.usefixtures("with_db")
def test_readyz_passes_when_postgres_answers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pinging(monkeypatch, _ok)

    r = client.get("/readyz")

    assert r.status_code == 200
    assert r.json() == {"status": "pass"}


@pytest.mark.usefixtures("with_db")
def test_readyz_fails_when_postgres_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pinging(monkeypatch, _refused)

    r = client.get("/readyz")

    assert r.status_code == 503
    assert r.json() == {"status": "fail", "output": "postgres: connection refused"}


@pytest.mark.usefixtures("with_db")
def test_readyz_fails_when_postgres_hangs(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def hangs(_: str) -> None:
        await asyncio.sleep(10)

    _pinging(monkeypatch, hangs)
    monkeypatch.setattr(health, "TIMEOUT_SECONDS", 0.05)

    r = client.get("/readyz")

    assert r.status_code == 503
    assert r.json() == {"status": "fail", "output": "postgres: timed out"}


def test_readyz_warns_without_a_database(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cfg, "postgres_dsn", "")

    r = client.get("/readyz")

    assert r.status_code == 200
    assert r.json()["status"] == "warn"
    assert "DVA_VC_MANAGER_DB_URL" in r.json()["output"]
