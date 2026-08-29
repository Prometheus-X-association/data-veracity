from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import (
    get_repo,
    get_requirement_validator,
    get_template_repo,
)
from vla_manager_api.main import create_app
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.vla_repo import FakeVLARepo

MISSING_ID = "00000000-0000-0000-0000-000000000099"

TEMPLATE = {
    "name": "Minimum record count",
    "criterionType": "GREATER_THAN",
    "targetAspect": "COMPLETENESS",
    "evaluationMethod": {
        "engine": "JQ",
        "variableSchema": {
            "type": "object",
            "properties": {"minimum": {"type": "integer"}},
            "required": ["minimum"],
        },
        "implementationTemplate": '.items | length as $count | {"success": ($count >= {{minimum}}), "details": "record count"}',
    },
}


class FakeRequirementValidator:
    def __init__(self) -> None:
        self.requests: list[dict[str, str]] = []
        self.response = {
            "valid": True,
            "status": "VALID",
            "code": "EVALUATION_LOGIC_VALID",
            "engine": "JQ",
            "message": "The evaluation logic is valid.",
            "details": None,
        }

    async def validate(self, engine: str, implementation: str) -> dict[str, Any]:
        self.requests.append({"engine": engine, "implementation": implementation})
        return self.response


class UnavailableRequirementValidator:
    async def validate(self, engine: str, implementation: str) -> dict[str, Any]:
        raise OSError("processing service is unavailable")


@pytest.fixture
def fake_template_repo() -> FakeTemplateRepo:
    return FakeTemplateRepo()


@pytest.fixture
def fake_validator() -> FakeRequirementValidator:
    return FakeRequirementValidator()


@pytest.fixture
def client(
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: FakeVLARepo()
    app.dependency_overrides[get_template_repo] = lambda: fake_template_repo
    app.dependency_overrides[get_requirement_validator] = lambda: fake_validator
    with TestClient(app) as test_client:
        yield test_client


def create_template(client: TestClient) -> str:
    response = client.post("/template", json=TEMPLATE)
    assert response.status_code == 201
    return response.json()["id"]


def test_validates_rendered_template_with_processing(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = create_template(client)

    response = client.post(
        f"/template/{template_id}/validate", json={"model": {"minimum": 2}}
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["implementation"].endswith(
        '{"success": ($count >= 2), "details": "record count"}'
    )
    assert fake_validator.requests == [
        {
            "engine": "JQ",
            "implementation": response.json()["implementation"],
        }
    ]


def test_rejects_missing_required_template_variable(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = create_template(client)

    response = client.post(f"/template/{template_id}/validate", json={"model": {}})

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["code"] == "TEMPLATE_INPUT_INVALID"
    assert "minimum" in response.json()["details"]
    assert fake_validator.requests == []


def test_returns_processing_validation_failure(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = create_template(client)
    fake_validator.response = {
        "valid": False,
        "status": "INVALID",
        "code": "EVALUATION_LOGIC_SYNTAX_INVALID",
        "engine": "JQ",
        "message": "The JQ implementation could not be compiled.",
        "details": "Unexpected token",
    }

    response = client.post(
        f"/template/{template_id}/validate", json={"model": {"minimum": 2}}
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["code"] == "EVALUATION_LOGIC_SYNTAX_INVALID"
    assert response.json()["implementation"]


def test_validation_reports_unknown_template(client: TestClient) -> None:
    response = client.post(
        f"/template/{MISSING_ID}/validate", json={"model": {"minimum": 2}}
    )

    assert response.status_code == 404


def test_reports_processing_unavailability_as_an_indeterminate_result(
    client: TestClient,
) -> None:
    template_id = create_template(client)
    client.app.dependency_overrides[get_requirement_validator] = (
        lambda: UnavailableRequirementValidator()
    )

    response = client.post(
        f"/template/{template_id}/validate", json={"model": {"minimum": 2}}
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["status"] == "UNAVAILABLE"
    assert response.json()["code"] == "EVALUATION_ENGINE_UNAVAILABLE"
    assert response.json()["implementation"]
