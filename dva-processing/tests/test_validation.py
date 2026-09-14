"""
Unit tests for static validation of a requirement's evaluation logic.

Covers, per engine, that logic which compiles is accepted and logic which
does not is reported as a verdict rather than an error; that an engine
which cannot be loaded is told apart from logic which is wrong; and that
an engine the service does not implement is still a ``400``.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from open_data_contract_standard.model import DataQuality

from dva_processing.engines import jq
from dva_processing.eval import UnknownEngineError
from dva_processing.http import create_app
from dva_processing.model import QualityEngine, RequirementValidationFailureReason
from dva_processing.validation import validate_requirement


def _requirement(engine: QualityEngine, implementation: Any) -> DataQuality:
    return DataQuality(engine=engine, implementation=implementation)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# --- JQ ---------------------------------------------------------------


def test_accepts_compilable_jq_expression() -> None:
    result = validate_requirement(
        _requirement(
            QualityEngine.jq,
            '.items | length as $count | {"success": ($count >= 2), "details": "n"}',
        )
    )

    assert result.valid is True
    assert result.engine == QualityEngine.jq


def test_rejects_invalid_jq_syntax() -> None:
    result = validate_requirement(_requirement(QualityEngine.jq, ".items | | length"))

    assert result.valid is False
    assert result.engine == QualityEngine.jq
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


# --- JSON Schema ------------------------------------------------------


def test_accepts_valid_json_schema() -> None:
    result = validate_requirement(
        _requirement(QualityEngine.schema, '{"type":"object","required":["id"]}')
    )

    assert result.valid is True
    assert result.engine == QualityEngine.schema


def test_rejects_invalid_json_schema_definition() -> None:
    result = validate_requirement(
        _requirement(QualityEngine.schema, '{"type":"not-a-json-schema-type"}')
    )

    assert result.valid is False
    assert result.engine == QualityEngine.schema
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


def test_rejects_json_schema_that_is_not_json() -> None:
    result = validate_requirement(
        _requirement(QualityEngine.schema, "{not json at all")
    )

    assert result.valid is False
    assert result.engine == QualityEngine.schema
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


# --- Great Expectations -----------------------------------------------


def test_accepts_valid_great_expectations_configuration() -> None:
    result = validate_requirement(
        _requirement(
            QualityEngine.great_expectations,
            """
type: ExpectColumnValuesToBeBetween
kwargs:
  column: temperature
  min_value: 0
  max_value: 100
""",
        )
    )

    assert result.valid is True
    assert result.engine == QualityEngine.great_expectations


def test_rejects_unknown_great_expectations_type() -> None:
    result = validate_requirement(
        _requirement(
            "GREAT_EXPECTATIONS",
            """
type: ExpectSomethingThatDoesNotExist
kwargs: {}
""",
        )
    )

    assert result.valid is False
    assert result.engine == QualityEngine.great_expectations
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


def test_rejects_great_expectations_implementation_that_is_not_yaml() -> None:
    result = validate_requirement(
        _requirement(QualityEngine.great_expectations, "type: [unclosed")
    )

    assert result.valid is False
    assert result.engine == QualityEngine.great_expectations
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


# --- Implementations that carry no logic ------------------------------


@pytest.mark.parametrize("implementation", ["   ", "", None, {"type": "object"}])
def test_rejects_an_implementation_that_is_not_logic(implementation: Any) -> None:
    result = validate_requirement(_requirement(QualityEngine.jq, implementation))

    assert result.valid is False
    assert result.engine == QualityEngine.jq
    assert result.reason == RequirementValidationFailureReason.invalid_implementation


# --- Engines the service cannot run -----------------------------------


def test_reports_an_engine_that_cannot_be_loaded_as_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An engine failing to load is not the author's expression being wrong."""

    def _unavailable(_: str) -> None:
        raise ImportError("libjq is missing")

    monkeypatch.setattr(jq, "compile_expression", _unavailable)

    result = validate_requirement(_requirement(QualityEngine.jq, ".items | length"))

    assert result.valid is False
    assert result.engine == QualityEngine.jq
    assert result.reason == RequirementValidationFailureReason.unavailable_engine
    assert "libjq is missing" in result.details


def test_an_unimplemented_engine_is_an_error_not_a_verdict() -> None:
    with pytest.raises(UnknownEngineError):
        validate_requirement(_requirement("SPARK_SQL", "SELECT 1"))


# --- The endpoint -----------------------------------------------------


def test_validation_endpoint_returns_structured_result(client: TestClient) -> None:
    response = client.post(
        "/validate-requirement",
        json={"engine": "JQ", "implementation": ".items | | length"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["engine"] == "JQ"
    assert body["reason"] == "INVALID_IMPLEMENTATION"


def test_validation_endpoint_accepts_a_full_odcs_entry(client: TestClient) -> None:
    """The body is an ODCS DataQuality, so its other fields must not trip it."""
    response = client.post(
        "/validate-requirement",
        json={
            "name": "At least two records",
            "type": "custom",
            "engine": "JQ",
            "implementation": ".items | length as $c | "
            '{"success": ($c >= 2), "details": "n"}',
        },
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validation_endpoint_reports_an_unimplemented_engine_as_400(
    client: TestClient,
) -> None:
    response = client.post(
        "/validate-requirement",
        json={"engine": "SPARK_SQL", "implementation": "SELECT 1"},
    )

    assert response.status_code == 400
    assert response.json()["type"] == "UNKNOWN_ENGINE"
