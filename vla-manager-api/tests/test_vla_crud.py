"""Unit tests for the VLA Manager API — VLA CRUD happy path.

Mirrors the Kotlin ``VLARoutesTest`` contract (the four operations it
covers): list, get-by-id, create, get-not-found. Adds an explicit
``DELETE /vla`` test covering the bulk wipe.

The tests override the ``get_repo`` dependency with an in-memory
``FakeVLARepo`` so no Postgres is required, and the requirement validator
with a fake so no DVA Processing is either.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import Any, Optional
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from open_data_contract_standard.model import OpenDataContractStandard

from vla_manager_api.dependencies import (
    get_repo,
    get_requirement_validator,
    get_template_repo,
)
from vla_manager_api.main import create_app
from vla_manager_api.models import (
    QualityEngine,
    TemplateNew,
    TemplateValidationResult,
    ValidationFailureReason,
)
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.validation import ProcessingError
from vla_manager_api.vla_repo import FakeVLARepo


class FakeRequirementValidator:
    """Accepts everything unless told to reject or to be unreachable."""

    def __init__(self) -> None:
        self.implementations: list[str] = []
        self.reject: set[str] = set()
        self.unavailable = False

    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult:
        self.implementations.append(implementation)
        if self.unavailable:
            raise ProcessingError("processing service is unavailable")
        reason: Optional[ValidationFailureReason] = None
        if implementation in self.reject:
            reason = ValidationFailureReason.invalid_implementation
        return TemplateValidationResult(
            valid=reason is None,
            reason=reason,
            engine=engine,
            details="compile error" if reason else None,
            implementation=implementation,
        )


@pytest.fixture
def fake_repo() -> FakeVLARepo:
    return FakeVLARepo()


@pytest.fixture
def fake_template_repo() -> FakeTemplateRepo:
    return FakeTemplateRepo()


@pytest.fixture
def fake_validator() -> FakeRequirementValidator:
    return FakeRequirementValidator()


@pytest.fixture
def client(
    fake_repo: FakeVLARepo,
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: fake_repo
    app.dependency_overrides[get_template_repo] = lambda: fake_template_repo
    app.dependency_overrides[get_requirement_validator] = lambda: fake_validator
    # As a context manager TestClient runs the lifespan, which is what
    # builds the repos onto app.state.
    with TestClient(app) as test_client:
        yield test_client


def test_list_vlas_empty_when_nothing_created(client: TestClient) -> None:
    r = client.get("/vla")
    assert r.status_code == 200
    assert r.json() == []


def test_get_vla_not_found(client: TestClient) -> None:
    r = client.get("/vla/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404


def test_create_vla_returns_id_and_appears_in_subsequent_gets(
    client: TestClient,
) -> None:
    schema = [
        {
            "name": "data",
            "quality": [{"engine": "JQ", "implementation": "{ success: true }"}],
        }
    ]
    payload = {"description": {"purpose": "Test VLA"}, "schema": schema}
    r = client.post("/vla", json=payload)
    assert r.status_code == 201
    body = r.json()

    new_id = UUID(body["id"])

    # The persisted VLA carries the wrapper boilerplate + injected id.
    r2 = client.get(f"/vla/{new_id}")
    assert r2.status_code == 200
    persisted = r2.json()
    assert persisted["id"] == str(new_id)
    assert persisted["description"] == {"purpose": "Test VLA"}
    assert persisted["apiVersion"] == "v3.0.2"
    assert persisted["kind"] == "DataContract"
    assert persisted["version"] == "0.1.0"
    assert persisted["status"] == "active"
    assert persisted["schema"] == schema


def test_create_vla_with_minimal_body_persists(client: TestClient) -> None:
    r = client.post("/vla", json={})
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    persisted = client.get(f"/vla/{new_id}").json()
    # Only the wrapper boilerplate + id should be present.
    assert persisted["apiVersion"] == "v3.0.2"
    assert persisted["kind"] == "DataContract"
    assert "description" not in persisted


def test_created_vla_then_listed(client: TestClient) -> None:
    # Create one
    r = client.post("/vla", json={"name": "My first VLA"})
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    # List shows it
    listing = client.get("/vla").json()
    assert len(listing) == 1
    assert listing[0]["id"] == str(new_id)
    assert listing[0]["name"] == "My first VLA"


def test_delete_all_removes_every_vla(client: TestClient) -> None:
    client.post("/vla", json={"name": "one"})
    client.post("/vla", json={"name": "two"})
    assert len(client.get("/vla").json()) == 2

    r = client.delete("/vla")
    assert r.status_code == 204
    assert client.get("/vla").json() == []


def test_vla_id_is_a_real_uuid_v4(client: TestClient) -> None:
    r = client.post("/vla", json={"name": "x"})
    new_id = UUID(r.json()["id"])
    # Version nibble of a UUIDv4 is 4 in the 13th hex digit.
    assert str(new_id)[14] == "4"


def test_vla_from_templates_returns_404_for_missing_template(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
) -> None:
    r = client.post(
        "/vla/from-templates",
        json={
            "qualityTemplates": [
                {"id": "00000000-0000-0000-0000-000000000099", "model": {}}
            ]
        },
    )
    assert r.status_code == 404


def test_vla_from_templates_creates_vla_with_rendered_quality(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
) -> None:
    # The repo mints the id, so the seeded template is referred to by what
    # `add` hands back rather than by one fixed here.
    template_id = asyncio.run(
        fake_template_repo.add(
            TemplateNew.model_validate(
                {
                    "name": "JQ check",
                    "criterionType": "VALID_INVALID",
                    "targetAspect": "SYNTAX",
                    "evaluationMethod": {
                        "engine": "JQ",
                        "variableSchema": {"value": {"type": "string"}},
                        "implementationTemplate": '.value == "ok"',
                    },
                }
            )
        )
    )
    r = client.post(
        "/vla/from-templates",
        json={
            "name": "rendered VLA",
            "qualityTemplates": [{"id": str(template_id), "model": {"value": "ok"}}],
        },
    )
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])
    vla = client.get(f"/vla/{new_id}").json()
    assert vla["name"] == "rendered VLA"
    # Without a schema of its own, the VLA gets one to hold its requirements.
    [schema_object] = vla["schema"]
    assert schema_object["name"] == "data"
    assert [q["engine"] for q in schema_object["quality"]] == ["JQ"]
    # Processing parses the VLA with this model during attestation.
    OpenDataContractStandard.model_validate(vla)


def _add_range_template(repo: FakeTemplateRepo) -> str:
    template_id = asyncio.run(
        repo.add(
            TemplateNew.model_validate(
                {
                    "name": "Range check",
                    "criterionType": "IN_RANGE",
                    "targetAspect": "ACCURACY",
                    "evaluationMethod": {
                        "engine": "JQ",
                        "variableSchema": {
                            "type": "object",
                            "properties": {"max": {"type": "integer"}},
                            "required": ["max"],
                        },
                        "implementationTemplate": "{success: (.value <= {{max}})}",
                    },
                }
            )
        )
    )
    return str(template_id)


def _from_templates(
    client: TestClient,
    *models: tuple[str, dict[str, Any]],
    **fields: Any,
):
    return client.post(
        "/vla/from-templates",
        json={
            "name": "checked VLA",
            **fields,
            "qualityTemplates": [{"id": tid, "model": m} for tid, m in models],
        },
    )


def test_vla_from_templates_persists_the_validated_implementation(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> None:
    template_id = _add_range_template(fake_template_repo)

    r = _from_templates(client, (template_id, {"max": 10}))

    assert r.status_code == 201, r.text
    assert fake_validator.implementations == ["{success: (.value <= 10)}"]
    vla = client.get(f"/vla/{r.json()['id']}").json()
    assert vla["schema"][0]["quality"] == [
        {
            "type": "custom",
            "engine": "JQ",
            "implementation": "{success: (.value <= 10)}",
        }
    ]


def test_vla_from_templates_adds_to_the_first_schema_object(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
) -> None:
    template_id = _add_range_template(fake_template_repo)
    own = {"type": "custom", "engine": "SCHEMA", "implementation": "{}"}
    schema = [
        {"name": "statement", "logicalType": "object", "quality": [own]},
        {"name": "other"},
    ]

    r = _from_templates(client, (template_id, {"max": 10}), schema=schema)

    assert r.status_code == 201, r.text
    vla = client.get(f"/vla/{r.json()['id']}").json()
    assert [q["engine"] for q in vla["schema"][0]["quality"]] == ["SCHEMA", "JQ"]
    assert vla["schema"][1] == {"name": "other"}


def test_vla_from_templates_rejects_input_outside_the_variable_schema(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> None:
    template_id = _add_range_template(fake_template_repo)

    r = _from_templates(client, (template_id, {"max": "ten"}))

    assert r.status_code == 400
    assert r.json()["type"] == "INVALID_REQUIREMENT"
    assert "Requirement 1 (Range check" in r.json()["title"]
    assert "variable schema" in r.json()["title"]
    # Input that does not fit the schema never reaches processing.
    assert fake_validator.implementations == []
    assert client.get("/vla").json() == []


def test_vla_from_templates_rejects_logic_processing_cannot_compile(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> None:
    template_id = _add_range_template(fake_template_repo)
    fake_validator.reject.add("{success: (.value <= 20)}")

    r = _from_templates(client, (template_id, {"max": 10}), (template_id, {"max": 20}))

    assert r.status_code == 400
    assert r.json()["type"] == "INVALID_REQUIREMENT"
    assert r.json()["title"].startswith("Requirement 2 (Range check")
    assert "compile error" in r.json()["title"]
    # The first requirement was fine, but the VLA is created whole or not
    # at all.
    assert client.get("/vla").json() == []


def test_vla_from_templates_refuses_when_processing_is_unavailable(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
    fake_validator: FakeRequirementValidator,
) -> None:
    template_id = _add_range_template(fake_template_repo)
    fake_validator.unavailable = True

    r = _from_templates(client, (template_id, {"max": 10}))

    assert r.status_code == 503
    assert r.json()["type"] == "VALIDATION_UNAVAILABLE"
    assert client.get("/vla").json() == []


def test_create_vla_with_schema_field_round_trips(client: TestClient) -> None:
    # The JSON key is literally ``schema`` (not ``schema_``); pydantic
    # field alias must accept it and persist it under that key.
    payload = {
        "name": "with-schema",
        "schema": [{"name": "xapi_statement", "logicalType": "object"}],
    }
    r = client.post("/vla", json=payload)
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    persisted = client.get(f"/vla/{new_id}").json()
    assert persisted["name"] == "with-schema"
    assert persisted["schema"] == [{"name": "xapi_statement", "logicalType": "object"}]
    # The internal pydantic field name ``schema_`` must never leak out.
    assert "schema_" not in persisted


# --- VLAs that are not ODCS, or that processing could not run ----------


@pytest.mark.parametrize(
    ("payload", "where"),
    [
        # The pre-ODCS shape, which attestation's processing refuses.
        (
            {"quality": [{"engine": "JQ", "implementation": "{success: true}"}]},
            "quality",
        ),
        ({"schema": [{"name": "data", "properties": "id"}]}, "schema.0.properties"),
        (
            {"schema": [{"quality": [{"engine": "SQL", "implementation": "x"}]}]},
            "schema.0.quality.0.engine",
        ),
        (
            {"schema": [{"quality": [{"engine": "JQ"}]}]},
            "schema.0.quality.0.implementation",
        ),
        (
            {
                "schema": [
                    {
                        "properties": [
                            {
                                "name": "id",
                                "quality": [{"engine": "JQ", "implementation": "true"}],
                            }
                        ]
                    }
                ]
            },
            "schema.0.properties.0.quality",
        ),
    ],
)
def test_create_vla_refuses_what_attestation_could_not_evaluate(
    client: TestClient, payload: dict[str, Any], where: str
) -> None:
    r = client.post("/vla", json=payload)

    assert r.status_code == 400, r.text
    assert r.json()["type"] == "INVALID_VLA"
    assert where in r.json()["title"]
    assert client.get("/vla").json() == []


def test_create_vla_refuses_a_plain_text_description(client: TestClient) -> None:
    # ODCS describes a contract with an object ({purpose, usage, …}).
    r = client.post("/vla", json={"description": "just text"})

    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "description"]


def test_a_vla_stored_in_the_pre_odcs_shape_is_read_as_odcs(
    client: TestClient, fake_repo: FakeVLARepo
) -> None:
    # Stored directly: the API no longer accepts this shape.
    legacy_id = asyncio.run(
        fake_repo.add(
            {
                "apiVersion": "v3.0.2",
                "kind": "DataContract",
                "version": "0.1.0",
                "status": "active",
                "name": "Test VLA",
                "description": "Asserts the year.",
                "schema": {"properties": {"timestamp": {"type": "string"}}},
                "quality": [{"engine": "JQ", "implementation": "{success: true}"}],
            }
        )
    )

    vla = client.get(f"/vla/{legacy_id}").json()

    assert vla["description"] == {"purpose": "Asserts the year."}
    assert vla["schema"] == [
        {
            "name": "data",
            "logicalType": "object",
            "properties": [{"name": "timestamp", "logicalType": "string"}],
            "quality": [
                {"type": "custom", "engine": "JQ", "implementation": "{success: true}"}
            ],
        }
    ]
    assert "quality" not in vla
    OpenDataContractStandard.model_validate(vla)
