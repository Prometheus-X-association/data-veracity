"""
Tests for running a template over sample data.

``POST /evaluate/from-template`` renders the template here and has DVA
Processing's ``/evaluate`` run it; processing is faked for the route, and the
client that really calls it is covered over a stubbed transport.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import (
    get_repo,
    get_requirement_evaluator,
    get_template_repo,
)
from vla_manager_api.main import create_app
from vla_manager_api.models import QualityEngine
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.validation import ProcessingError, ProcessingRequirementValidator
from vla_manager_api.vla_repo import FakeVLARepo

TEMPLATE = {
    "name": "Allowed keys",
    "criterionType": "VALID_INVALID",
    "targetAspect": "SYNTAX",
    "evaluationMethod": {
        "engine": "SCHEMA",
        "variableSchema": {
            "type": "object",
            "properties": {"keys": {"type": "array", "items": {"type": "string"}}},
            "required": ["keys"],
        },
        "implementationTemplate": '{"type": "object", "propertyNames": {"enum": {{{keys}}}}}',
    },
}

RESULT = {
    "engine": "SCHEMA",
    "timestamp": "2026-09-24T12:00:00Z",
    "success": True,
    "details": "The data conforms to the schema.",
}


class FakeEvaluator:
    """Answers as processing's client would, without the network."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.answer: tuple[int, Any] = (200, RESULT)
        self.unavailable = False

    async def evaluate(
        self, engine: QualityEngine, implementation: str, data: Any
    ) -> tuple[int, Any]:
        self.calls.append(
            {"engine": engine, "implementation": implementation, "data": data}
        )
        if self.unavailable:
            raise ProcessingError("processing service is unavailable")
        return self.answer


@pytest.fixture
def evaluator() -> FakeEvaluator:
    return FakeEvaluator()


@pytest.fixture
def client(evaluator: FakeEvaluator) -> Iterator[TestClient]:
    repo = FakeTemplateRepo()
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: FakeVLARepo()
    app.dependency_overrides[get_template_repo] = lambda: repo
    app.dependency_overrides[get_requirement_evaluator] = lambda: evaluator
    with TestClient(app) as test_client:
        yield test_client


def _template(client: TestClient) -> str:
    response = client.post("/template", json=TEMPLATE)
    assert response.status_code == 201
    return response.json()["id"]


def _evaluate(client: TestClient, template_id: str, model: dict, data: Any):
    return client.post(
        "/evaluate/from-template",
        json={"templateID": template_id, "templateModel": model, "data": data},
    )


def test_renders_the_template_and_has_processing_run_it(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    template_id = _template(client)

    response = _evaluate(client, template_id, {"keys": ["id"]}, {"id": 1})

    assert response.status_code == 200, response.text
    assert response.json() == RESULT
    assert evaluator.calls == [
        {
            "engine": QualityEngine.SCHEMA,
            "implementation": '{"type": "object", "propertyNames": {"enum": ["id"]}}',
            "data": {"id": 1},
        }
    ]


def test_passes_a_failed_evaluation_through_as_processing_reported_it(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    template_id = _template(client)
    failed = {**RESULT, "success": False, "error": "engine crashed"}
    evaluator.answer = (500, failed)

    response = _evaluate(client, template_id, {"keys": ["id"]}, {"other": 1})

    assert response.status_code == 500
    assert response.json() == failed


def test_reports_an_unknown_template(client: TestClient) -> None:
    response = _evaluate(
        client, "00000000-0000-0000-0000-000000000099", {"keys": []}, {}
    )

    assert response.status_code == 404


def test_rejects_input_outside_the_variable_schema(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    template_id = _template(client)

    response = _evaluate(client, template_id, {"keys": "id"}, {})

    assert response.status_code == 400
    assert response.json()["type"] == "INVALID_TEMPLATE_INPUT"
    assert evaluator.calls == []


def test_reports_processing_being_unreachable(
    client: TestClient, evaluator: FakeEvaluator
) -> None:
    template_id = _template(client)
    evaluator.unavailable = True

    response = _evaluate(client, template_id, {"keys": ["id"]}, {})

    assert response.status_code == 503
    assert response.json()["type"] == "EVALUATION_UNAVAILABLE"


def test_accepts_the_request_processing_itself_accepts(client: TestClient) -> None:
    """The DVA's ``templateID`` spelling, not ``templateId``."""
    template_id = _template(client)

    response = client.post(
        "/evaluate/from-template",
        json={"templateId": template_id, "templateModel": {"keys": []}, "data": {}},
    )

    assert response.status_code == 422


async def test_the_client_sends_processing_an_evaluation_request() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=RESULT)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    async with ProcessingRequirementValidator(
        "http://processing:5000/", client=client
    ) as processing:
        code, body = await processing.evaluate(
            QualityEngine.JQ, "{success: true}", {"a": 1}
        )

    assert (code, body) == (200, RESULT)
    assert str(seen[0].url) == "http://processing:5000/evaluate"
    assert json.loads(seen[0].read()) == {
        "requirement": {"engine": "JQ", "implementation": "{success: true}"},
        "data": {"a": 1},
    }


async def test_the_client_raises_when_processing_cannot_be_reached() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route to host")

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    async with ProcessingRequirementValidator(
        "http://processing:5000", client=client
    ) as processing:
        with pytest.raises(ProcessingError, match="Request to DVA Processing failed"):
            await processing.evaluate(QualityEngine.JQ, "{success: true}", {})
