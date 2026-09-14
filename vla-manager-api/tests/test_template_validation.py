"""
Tests for validating a rendered template's evaluation logic.

The route is covered through fakes standing in for DVA Processing; the
client that really talks to it is covered separately at the bottom, over a
stubbed transport, since it is the piece that turns a network failure into
the ``UNAVAILABLE_ENGINE`` verdict the rest of this relies on.
"""

from collections.abc import Iterator
from typing import Any, Optional

import httpx2
import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import (
    get_repo,
    get_requirement_validator,
    get_template_repo,
)
from vla_manager_api.main import create_app
from vla_manager_api.models import (
    QualityEngine,
    TemplateValidationResult,
    ValidationFailureReason,
)
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.validation import (
    ProcessingError,
    ProcessingRequirementValidator,
)
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

validate_request_good = {"minimum": 2}


def _validate(client: TestClient, template_id: str, body: dict):
    return client.post(f"/template/{template_id}/validate", json=body)


def _result(response) -> TemplateValidationResult:
    """Read the response back as the model the route declares."""
    return TemplateValidationResult.model_validate(response.json())


class FakeRequirementValidator:
    """Answers as processing's client would, without the network."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.reason: Optional[ValidationFailureReason] = None
        self.details: Optional[str] = None

    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult:
        self.requests.append({"engine": engine, "implementation": implementation})
        return TemplateValidationResult(
            valid=self.reason is None,
            reason=self.reason,
            engine=engine,
            details=self.details,
            implementation=implementation,
        )


class UnavailableRequirementValidator:
    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult:
        raise ProcessingError("processing service is unavailable")


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


def _create_template(client: TestClient) -> str:
    response = client.post("/template", json=TEMPLATE)
    assert response.status_code == 201
    return response.json()["id"]


def test_validates_rendered_template_with_processing(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = _create_template(client)
    response = _validate(client, template_id, validate_request_good)
    result = _result(response)

    assert response.status_code == 200
    assert result.valid is True
    assert fake_validator.requests == [
        {
            "engine": result.engine,
            "implementation": result.implementation,
        }
    ]


def test_a_pass_omits_the_fields_it_has_no_value_for(client: TestClient) -> None:
    """The spec has `reason` absent on a pass, not present and null."""
    template_id = _create_template(client)

    body = _validate(client, template_id, validate_request_good).json()

    assert body["valid"] is True
    assert "reason" not in body
    assert "details" not in body


def test_rejects_missing_required_template_variable(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = _create_template(client)

    response = _validate(client, template_id, {})
    result = _result(response)

    assert response.status_code == 200
    assert result.valid is False
    assert result.reason == ValidationFailureReason.invalid_implementation
    assert "minimum" in result.details
    assert fake_validator.requests == []


def test_returns_processing_validation_failure(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    template_id = _create_template(client)
    fake_validator.reason = ValidationFailureReason.invalid_implementation
    fake_validator.details = "The JQ implementation could not be compiled."

    response = _validate(client, template_id, validate_request_good)
    result = _result(response)

    assert response.status_code == 200
    assert result.valid is False
    assert result.reason == ValidationFailureReason.invalid_implementation
    assert result.details == fake_validator.details
    assert result.implementation


def test_validation_reports_unknown_template(client: TestClient) -> None:
    response = _validate(client, MISSING_ID, validate_request_good)

    assert response.status_code == 404


def test_reports_processing_unavailability_as_an_indeterminate_result(
    client: TestClient,
) -> None:
    template_id = _create_template(client)
    client.app.dependency_overrides[get_requirement_validator] = lambda: (
        UnavailableRequirementValidator()
    )

    response = _validate(client, template_id, validate_request_good)
    result = _result(response)

    assert response.status_code == 200
    assert result.valid is False
    assert result.reason == ValidationFailureReason.unavailable_engine
    assert result.implementation


def test_reports_a_template_that_cannot_be_rendered(
    client: TestClient, fake_validator: FakeRequirementValidator
) -> None:
    """A malformed stored template is the template's fault, not the model's."""
    broken = {
        **TEMPLATE,
        "evaluationMethod": {
            **TEMPLATE["evaluationMethod"],
            "implementationTemplate": "{{#unclosed}} .items | length",
        },
    }
    template_id = client.post("/template", json=broken).json()["id"]

    response = _validate(client, template_id, validate_request_good)
    result = _result(response)

    assert response.status_code == 200
    assert result.valid is False
    assert result.reason == ValidationFailureReason.invalid_implementation
    assert result.implementation is None
    assert "implementation" not in response.json()
    assert fake_validator.requests == []


# --- The client that really talks to DVA Processing --------------------


def validator_over(handler) -> ProcessingRequirementValidator:
    """A validator whose HTTP calls are answered by ``handler``."""
    return ProcessingRequirementValidator(
        # Trailing slash on purpose: it must not double up in the path.
        "http://processing:5000/",
        client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )


async def test_the_client_posts_the_requirement_to_processing() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(
            200,
            json={
                "valid": True,
                "status": "VALID",
                "code": "EVALUATION_LOGIC_VALID",
                "engine": "JQ",
                "message": "The evaluation logic is valid.",
            },
        )

    async with validator_over(handler) as validator:
        result = await validator.validate(QualityEngine.JQ, ".items | length")

    assert result.valid is True
    assert result.reason is None
    # Echoed back, so the route can return the client's result as it stands.
    assert result.implementation == ".items | length"

    assert str(seen[0].url) == "http://processing:5000/validate-requirement"
    assert seen[0].read() == b'{"engine":"JQ","implementation":".items | length"}'


async def test_the_client_reports_rejected_logic_as_a_verdict() -> None:
    """Processing rejecting the logic is an answer, not a ProcessingError."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "valid": False,
                "status": "INVALID",
                "message": "The jq implementation could not be compiled.",
                "details": "syntax error, unexpected '|'",
            },
        )

    async with validator_over(handler) as validator:
        result = await validator.validate(QualityEngine.JQ, ".items | | length")

    assert result.valid is False
    assert result.reason is ValidationFailureReason.invalid_implementation
    # Processing's message and its underlying error, joined for the author.
    assert result.details == (
        "The jq implementation could not be compiled.\nsyntax error, unexpected '|'"
    )


async def test_the_client_reports_an_unloadable_engine_as_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "valid": False,
                "status": "UNAVAILABLE",
                "message": "The evaluation engine is unavailable.",
            },
        )

    async with validator_over(handler) as validator:
        result = await validator.validate(QualityEngine.JQ, ".items | length")

    assert result.valid is False
    assert result.reason is ValidationFailureReason.unavailable_engine


async def test_the_client_raises_when_processing_cannot_be_reached() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route to host")

    async with validator_over(handler) as validator:
        with pytest.raises(ProcessingError, match="Request to DVA Processing failed"):
            await validator.validate(QualityEngine.JQ, ".items | length")


async def test_the_client_raises_on_an_error_status() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(500, json={"title": "boom"})

    async with validator_over(handler) as validator:
        with pytest.raises(ProcessingError, match="Unusable DVA Processing response"):
            await validator.validate(QualityEngine.JQ, ".items | length")


async def test_the_client_raises_on_a_status_it_cannot_name() -> None:
    """A failure with no reason to report is not one to pass off as valid."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={"valid": False, "status": "SOMETHING_NEW", "message": "hm"},
        )

    async with validator_over(handler) as validator:
        with pytest.raises(ProcessingError, match="unknown status SOMETHING_NEW"):
            await validator.validate(QualityEngine.JQ, ".items | length")


async def test_the_client_raises_on_a_response_it_cannot_map() -> None:
    """A result missing fields must not reach the route as a KeyError."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"valid": True})

    async with validator_over(handler) as validator:
        with pytest.raises(ProcessingError, match="message, status"):
            await validator.validate(QualityEngine.JQ, ".items | length")
