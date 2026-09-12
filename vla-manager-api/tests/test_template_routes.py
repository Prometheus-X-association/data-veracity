"""
Unit tests for the VLA Template endpoints.

Covers all seven routes of ``template_routes``: list, create, fetch,
partial update, delete-one, delete-all and render. The validation cases
track ``docs/spec/vla-manager-api.yaml`` — the enums, the
``additionalProperties: false`` on template payloads, and the
``{type, title}`` error shape.

The tests override the repository dependencies with the in-memory
``FakeTemplateRepo`` so no Postgres is required.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import get_repo, get_template_repo
from vla_manager_api.main import create_app
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.vla_repo import FakeVLARepo

MISSING_ID = "00000000-0000-0000-0000-000000000099"

A_TEMPLATE = {
    "name": "Date matches",
    "description": "Checks the record date against a supplied value",
    "criterionType": "VALID_INVALID",
    "targetAspect": "SYNTAX",
    "evaluationMethod": {
        "engine": "JQ",
        "variableSchema": {"properties": {"date": {"type": "string"}}},
        "implementationTemplate": '{ success: .date == "{{ date }}" }',
    },
}


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


def _create(client: TestClient, **overrides: object) -> str:
    """Create a template and return its id."""
    r = client.post("/template", json={**A_TEMPLATE, **overrides})
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- list + create -----------------------------------------------------


def test_list_templates_empty_when_nothing_created(client: TestClient) -> None:
    r = client.get("/template")
    assert r.status_code == 200
    assert r.json() == []


def test_create_template_returns_a_uuid(client: TestClient) -> None:
    r = client.post("/template", json=A_TEMPLATE)
    assert r.status_code == 201
    # Raises if the id is not a well-formed UUID.
    UUID(r.json()["id"])


def test_created_template_appears_in_the_listing(client: TestClient) -> None:
    new_id = _create(client)

    listing = client.get("/template").json()
    assert [t["id"] for t in listing] == [new_id]
    assert listing[0]["name"] == A_TEMPLATE["name"]


def test_listing_returns_every_template(client: TestClient) -> None:
    ids = {_create(client, name="one"), _create(client, name="two")}

    assert {t["id"] for t in client.get("/template").json()} == ids


# --- fetch by id -------------------------------------------------------


def test_get_template_round_trips_every_field_in_camel_case(
    client: TestClient,
) -> None:
    new_id = _create(client)

    body = client.get(f"/template/{new_id}").json()
    assert body["id"] == new_id
    assert body["name"] == A_TEMPLATE["name"]
    assert body["description"] == A_TEMPLATE["description"]
    assert body["criterionType"] == "VALID_INVALID"
    assert body["targetAspect"] == "SYNTAX"
    assert body["evaluationMethod"] == A_TEMPLATE["evaluationMethod"]
    # The snake_case attribute names must never reach the wire.
    assert "criterion_type" not in body
    assert "variable_schema" not in body["evaluationMethod"]


def test_get_template_not_found(client: TestClient) -> None:
    assert client.get(f"/template/{MISSING_ID}").status_code == 404


# --- create validation (spec: enums + additionalProperties false) ------


def test_create_template_rejects_a_body_missing_required_fields(
    client: TestClient,
) -> None:
    assert client.post("/template", json={"name": "only-a-name"}).status_code == 422


def test_create_template_rejects_unknown_fields(client: TestClient) -> None:
    r = client.post("/template", json={**A_TEMPLATE, "bogusField": "x"})
    assert r.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("criterionType", "NOT_A_CRITERION"),
        ("targetAspect", "NOT_AN_ASPECT"),
    ],
)
def test_create_template_rejects_out_of_enum_values(
    client: TestClient, field: str, value: str
) -> None:
    assert (
        client.post("/template", json={**A_TEMPLATE, field: value}).status_code == 422
    )


def test_create_template_rejects_an_unknown_engine(client: TestClient) -> None:
    body = {
        **A_TEMPLATE,
        "evaluationMethod": {**A_TEMPLATE["evaluationMethod"], "engine": "COBOL"},
    }
    assert client.post("/template", json=body).status_code == 422


@pytest.mark.parametrize("engine", ["SCHEMA", "GREAT_EXPECTATIONS", "JQ"])
def test_create_template_accepts_every_spec_engine(
    client: TestClient, engine: str
) -> None:
    body = {
        **A_TEMPLATE,
        "evaluationMethod": {**A_TEMPLATE["evaluationMethod"], "engine": engine},
    }
    assert client.post("/template", json=body).status_code == 201


# --- patch -------------------------------------------------------------


def test_patch_updates_only_the_supplied_fields(client: TestClient) -> None:
    new_id = _create(client)

    r = client.patch(f"/template/{new_id}", json={"id": new_id, "name": "renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "renamed"
    # Everything else is left alone.
    assert r.json()["targetAspect"] == "SYNTAX"
    assert r.json()["evaluationMethod"] == A_TEMPLATE["evaluationMethod"]

    assert client.get(f"/template/{new_id}").json()["name"] == "renamed"


def test_patch_can_replace_the_evaluation_method(client: TestClient) -> None:
    new_id = _create(client)
    replacement = {
        "engine": "SCHEMA",
        "variableSchema": {"properties": {"n": {"type": "integer"}}},
        "implementationTemplate": "{{ n }}",
    }

    r = client.patch(
        f"/template/{new_id}", json={"id": new_id, "evaluationMethod": replacement}
    )
    assert r.status_code == 200
    assert r.json()["evaluationMethod"] == replacement


def test_patch_rejects_a_body_id_that_differs_from_the_path(
    client: TestClient,
) -> None:
    new_id = _create(client)

    r = client.patch(f"/template/{new_id}", json={"id": MISSING_ID, "name": "x"})
    assert r.status_code == 400
    assert r.json()["title"] == "ID path parameter does not match ID in body"


def test_patch_not_found(client: TestClient) -> None:
    r = client.patch(f"/template/{MISSING_ID}", json={"id": MISSING_ID, "name": "x"})
    assert r.status_code == 404


def test_patch_rejects_out_of_enum_values(client: TestClient) -> None:
    new_id = _create(client)

    r = client.patch(
        f"/template/{new_id}", json={"id": new_id, "criterionType": "NOPE"}
    )
    assert r.status_code == 422


# --- delete ------------------------------------------------------------


def test_delete_template_removes_it(client: TestClient) -> None:
    new_id = _create(client)

    assert client.delete(f"/template/{new_id}").status_code == 204
    assert client.get(f"/template/{new_id}").status_code == 404
    assert client.get("/template").json() == []


def test_delete_template_not_found(client: TestClient) -> None:
    assert client.delete(f"/template/{MISSING_ID}").status_code == 404


def test_delete_all_templates_wipes_the_collection(client: TestClient) -> None:
    _create(client, name="one")
    _create(client, name="two")

    assert client.delete("/template").status_code == 204
    assert client.get("/template").json() == []


# --- render ------------------------------------------------------------


def test_render_substitutes_the_model_into_the_template(client: TestClient) -> None:
    new_id = _create(client)

    r = client.post(f"/template/{new_id}/render", json={"date": "20250101T000000Z"})
    assert r.status_code == 200
    assert r.json() == {
        "engine": "JQ",
        "implementation": '{ success: .date == "20250101T000000Z" }',
    }


def test_render_not_found(client: TestClient) -> None:
    assert client.post(f"/template/{MISSING_ID}/render", json={}).status_code == 404


def test_render_reports_a_malformed_template_as_a_bad_request(
    client: TestClient,
) -> None:
    # An unclosed section is a template authoring error, not a bad model.
    broken = {
        **A_TEMPLATE["evaluationMethod"],
        "implementationTemplate": "{{#unclosed",
    }
    new_id = _create(client, evaluationMethod=broken)

    r = client.post(f"/template/{new_id}/render", json={})
    assert r.status_code == 400
    assert r.json()["title"] == "Failed to render template"


# --- error shape (spec: Error {type, title}) ---------------------------


@pytest.mark.parametrize(
    ("verb", "path", "body"),
    [
        ("get", f"/template/{MISSING_ID}", None),
        ("delete", f"/template/{MISSING_ID}", None),
        ("patch", f"/template/{MISSING_ID}", {"id": MISSING_ID, "name": "x"}),
        ("post", f"/template/{MISSING_ID}/render", {}),
    ],
)
def test_errors_use_the_spec_problem_shape(
    client: TestClient, verb: str, path: str, body: dict | None
) -> None:
    kwargs = {"json": body} if body is not None else {}
    r = getattr(client, verb)(path, **kwargs)

    assert r.status_code == 404
    assert set(r.json()) == {"type", "title"}
    assert r.json()["type"] == "NOT_FOUND"
    assert isinstance(r.json()["title"], str) and r.json()["title"]
