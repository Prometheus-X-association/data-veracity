"""
Tests for trying a stored VLA out on sample data.

``POST /vla/{id}/evaluate`` runs each of the VLA's requirements through DVA
Processing's ``/evaluate`` and attests nothing; processing is faked.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import get_repo, get_requirement_evaluator
from vla_manager_api.main import create_app
from vla_manager_api.models import QualityEngine
from vla_manager_api.validation import ProcessingError
from vla_manager_api.vla_repo import FakeVLARepo

QUALITY = [
    {"engine": "JQ", "implementation": "{success: (.id != null), details: \"id\"}"},
    {"engine": "SCHEMA", "implementation": '{"type": "object"}'},
]


def _result(engine: str, success: bool, **extra: Any) -> dict[str, Any]:
    return {
        "engine": engine,
        "timestamp": "2026-09-25T12:00:00Z",
        "success": success,
        **extra,
    }


class FakeEvaluator:
    """Answers each implementation as told, as processing's client would."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.answers: dict[str, tuple[int, Any]] = {}
        self.unavailable = False

    async def evaluate(
        self, engine: QualityEngine, implementation: str, data: Any
    ) -> tuple[int, Any]:
        self.calls.append(
            {"engine": engine, "implementation": implementation, "data": data}
        )
        if self.unavailable:
            raise ProcessingError("processing service is unavailable")
        return self.answers.get(
            implementation, (200, _result(engine.value, True, details="ok"))
        )


@pytest.fixture
def evaluator() -> FakeEvaluator:
    return FakeEvaluator()


@pytest.fixture
def client(evaluator: FakeEvaluator) -> Iterator[TestClient]:
    repo = FakeVLARepo()
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_requirement_evaluator] = lambda: evaluator
    with TestClient(app) as test_client:
        yield test_client


def _vla(client: TestClient, quality: list[dict[str, Any]] = QUALITY) -> str:
    response = client.post("/vla", json={"name": "Sample VLA", "quality": quality})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_runs_every_requirement_over_the_data_in_order(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    vla_id = _vla(client)

    response = client.post(f"/vla/{vla_id}/evaluate", json={"data": {"id": 1}})

    assert response.status_code == 200, response.text
    assert [r["success"] for r in response.json()] == [True, True]
    assert evaluator.calls == [
        {
            "engine": QualityEngine.JQ,
            "implementation": QUALITY[0]["implementation"],
            "data": {"id": 1},
        },
        {
            "engine": QualityEngine.SCHEMA,
            "implementation": QUALITY[1]["implementation"],
            "data": {"id": 1},
        },
    ]


def test_reports_a_failed_and_a_broken_requirement_as_results(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    vla_id = _vla(client)
    failed = _result("JQ", False, details="no id")
    broken = _result("SCHEMA", False, error="engine crashed")
    evaluator.answers = {
        QUALITY[0]["implementation"]: (200, failed),
        QUALITY[1]["implementation"]: (500, broken),
    }

    response = client.post(f"/vla/{vla_id}/evaluate", json={"data": {}})

    assert response.status_code == 200
    assert response.json() == [failed, broken]


def test_a_requirement_processing_refuses_becomes_a_failed_result(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    vla_id = _vla(client, QUALITY[:1])
    evaluator.answers = {
        QUALITY[0]["implementation"]: (
            400,
            {"type": "BAD_REQUEST", "title": "Unsupported engine"},
        )
    }

    response = client.post(f"/vla/{vla_id}/evaluate", json={"data": {}})

    assert response.status_code == 200
    [result] = response.json()
    assert result["success"] is False
    assert result["engine"] == "JQ"
    assert result["error"] == "Unsupported engine"
    assert result["timestamp"]


def test_a_vla_without_requirements_yields_no_results(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    vla_id = _vla(client, [])

    response = client.post(f"/vla/{vla_id}/evaluate", json={"data": {}})

    assert response.status_code == 200
    assert response.json() == []
    assert evaluator.calls == []


def test_reports_an_unknown_vla(client: TestClient) -> None:
    response = client.post(
        "/vla/00000000-0000-0000-0000-000000000099/evaluate", json={"data": {}}
    )

    assert response.status_code == 404


def test_reports_processing_being_unreachable(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    vla_id = _vla(client)
    evaluator.unavailable = True

    response = client.post(f"/vla/{vla_id}/evaluate", json={"data": {}})

    assert response.status_code == 503
    assert response.json()["type"] == "EVALUATION_UNAVAILABLE"


def test_requires_the_data(client: TestClient) -> None:
    vla_id = _vla(client)

    response = client.post(f"/vla/{vla_id}/evaluate", json={})

    assert response.status_code == 422
