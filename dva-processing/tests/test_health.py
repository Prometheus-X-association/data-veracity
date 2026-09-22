"""Tests for ``GET /livez`` and ``GET /readyz``."""

import pytest
from fastapi.testclient import TestClient

from dva_processing.http import create_app


@pytest.mark.parametrize("path", ["/livez", "/readyz"])
def test_health_passes(path: str) -> None:
    r = TestClient(create_app()).get(path)

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/health+json"
    assert r.json() == {"status": "pass"}
