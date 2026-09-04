from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import get_repo, get_template_repo
from vla_manager_api.main import create_app
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.vla_repo import FakeVLARepo


@pytest.fixture
def fake_template_repo() -> FakeTemplateRepo:
    return FakeTemplateRepo()


@pytest.fixture
def client(fake_template_repo: FakeTemplateRepo) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: FakeVLARepo()
    app.dependency_overrides[get_template_repo] = lambda: fake_template_repo
    with TestClient(app) as test_client:
        yield test_client


def test_assistant_returns_a_structured_template_proposal(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_complete(_messages: list[dict[str, str]]) -> str:
        return '{"message":"Prepared a schema template.","proposal":{"name":"xAPI schema","description":"Checks xAPI data.","criterionType":"VALID_INVALID","targetAspect":"SYNTAX","evaluationMethod":{"engine":"SCHEMA","variableSchema":{"type":"object","properties":{},"required":[]},"implementationTemplate":"{\\"type\\": \\"object\\"}"}},"examples":{"passing":{},"failing":{}}}'

    monkeypatch.setattr(
        "vla_manager_api.assistant_routes.complete_assistant", fake_complete
    )

    response = client.post(
        "/assistant/template",
        json={"message": "Check that this data follows the xAPI JSON schema."},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["proposal"]["evaluationMethod"]["engine"] == "SCHEMA"
    assert body["examples"] == {"passing": {}, "failing": {}}


def test_assistant_rejects_an_empty_message(client: TestClient) -> None:
    response = client.post("/assistant/template", json={"message": "  "})

    assert response.status_code == 422


def test_assistant_rejects_malformed_model_output(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_complete(_messages: list[dict[str, str]]) -> str:
        return "not json"

    monkeypatch.setattr(
        "vla_manager_api.assistant_routes.complete_assistant", fake_complete
    )

    response = client.post(
        "/assistant/template", json={"message": "Create a freshness check."}
    )

    assert response.status_code == 502
    assert response.json()["type"] == "ASSISTANT_INVALID_RESPONSE"


def test_assistant_rejects_a_proposal_outside_the_template_schema(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_complete(_messages: list[dict[str, str]]) -> str:
        return '{"message":"Prepared a draft.","proposal":{"name":"bad","criterionType":"VALID_INVALID","targetAspect":"SYNTAX","evaluationMethod":{"engine":"UNSUPPORTED","variableSchema":{},"implementationTemplate":"x"}}}'

    monkeypatch.setattr(
        "vla_manager_api.assistant_routes.complete_assistant", fake_complete
    )

    response = client.post(
        "/assistant/template", json={"message": "Create a template."}
    )

    assert response.status_code == 502
    assert response.json()["type"] == "ASSISTANT_INVALID_RESPONSE"


def test_assistant_reports_missing_model_configuration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("vla_manager_api.assistant.cfg.ai_url", "")

    response = client.post(
        "/assistant/template", json={"message": "Create a schema check."}
    )

    assert response.status_code == 503
    assert response.json()["type"] == "ASSISTANT_UNAVAILABLE"
