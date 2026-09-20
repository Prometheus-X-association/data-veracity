from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import get_repo, get_template_repo
from vla_manager_api.main import create_app
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.vla_repo import FakeVLARepo


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode()

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


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


def test_assistant_rejects_prose_where_a_schema_implementation_is_required(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_complete(_messages: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "message": "Prepared a draft.",
                "proposal": {
                    "name": "Production schema",
                    "description": "Checks production records.",
                    "criterionType": "VALID_INVALID",
                    "targetAspect": "SYNTAX",
                    "evaluationMethod": {
                        "engine": "SCHEMA",
                        "variableSchema": {"type": "object"},
                        "implementationTemplate": "Check that production_kwh is present.",
                    },
                },
            }
        )

    monkeypatch.setattr(
        "vla_manager_api.assistant_routes.complete_assistant", fake_complete
    )

    response = client.post(
        "/assistant/template", json={"message": "Create a production schema."}
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


def test_assistant_prompt_describes_the_template_enums_and_examples_shape() -> None:
    from vla_manager_api.assistant import build_assistant_messages

    system_prompt = build_assistant_messages("draft", [], [], None)[0]["content"]

    assert (
        "criterionType must be one of VALID_INVALID, IN_RANGE, GREATER_THAN, LESS_THAN"
        in system_prompt
    )
    assert (
        "targetAspect must be one of SYNTAX, TIMELINESS, ACCURACY, COMPLETENESS, CONSISTENCY"
        in system_prompt
    )
    assert (
        'examples must be an object with "passing" and "failing" values'
        in system_prompt
    )
    assert "at least two representative examples" in system_prompt
    assert (
        "SCHEMA implementationTemplate must be a string containing valid JSON Schema"
        in system_prompt
    )
    assert (
        "JQ implementationTemplate must be the executable jq expression"
        in system_prompt
    )
    assert (
        "GREAT_EXPECTATIONS implementationTemplate must be a string containing valid YAML"
        in system_prompt
    )


def test_gemini_uses_its_openai_compatible_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vla_manager_api import assistant

    monkeypatch.setattr(assistant.cfg, "ai_provider", "gemini")
    monkeypatch.setattr(assistant.cfg, "ai_url", "")
    monkeypatch.setattr(assistant.cfg, "ai_model", "")
    monkeypatch.setattr(assistant.cfg, "ai_api_key", "gemini-test-key")
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse({"choices": [{"message": {"content": '{"message":"ok"}'}}]})

    monkeypatch.setattr(assistant, "urlopen", fake_urlopen)

    result = assistant._complete_sync([{"role": "user", "content": "hello"}])

    request = captured["request"]
    assert result == '{"message":"ok"}'
    assert request.full_url == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )
    assert request.headers["Authorization"] == "Bearer gemini-test-key"
    assert request.headers["X-goog-api-client"] == "prometheus-x-data-veracity/0.1"
    body = json.loads(request.data)
    assert body["model"] == "gemini-3.1-flash-lite"


def test_anthropic_uses_messages_api_headers_and_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vla_manager_api import assistant

    monkeypatch.setattr(assistant.cfg, "ai_provider", "anthropic")
    monkeypatch.setattr(assistant.cfg, "ai_url", "https://api.anthropic.com/v1")
    monkeypatch.setattr(assistant.cfg, "ai_model", "claude-test")
    monkeypatch.setattr(assistant.cfg, "ai_api_key", "anthropic-test-key")
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse({"content": [{"type": "text", "text": '{"message":"ok"}'}]})

    monkeypatch.setattr(assistant, "urlopen", fake_urlopen)

    result = assistant._complete_sync(
        [
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": "hello"},
        ]
    )

    request = captured["request"]
    assert result == '{"message":"ok"}'
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.headers["X-api-key"] == "anthropic-test-key"
    assert request.headers["Anthropic-version"] == "2023-06-01"
    assert "Authorization" not in request.headers
    body = json.loads(request.data)
    assert body["model"] == "claude-test"
    assert body["system"] == "Return JSON only."
    assert body["messages"] == [{"role": "user", "content": "hello"}]
