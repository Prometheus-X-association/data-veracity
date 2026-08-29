from fastapi.testclient import TestClient

from dva_processing.http import app
from dva_processing.model import QualityEngine, Requirement
from dva_processing.validation import validate_requirement


def test_accepts_compilable_jq_expression():
    result = validate_requirement(
        Requirement(
            engine=QualityEngine.jq,
            implementation='.items | length as $count | {"success": ($count >= 2), "details": "record count"}',
        )
    )

    assert result.valid is True
    assert result.status == "VALID"
    assert result.code == "EVALUATION_LOGIC_VALID"


def test_rejects_invalid_jq_syntax():
    result = validate_requirement(
        Requirement(engine=QualityEngine.jq, implementation=".items | | length")
    )

    assert result.valid is False
    assert result.status == "INVALID"
    assert result.code == "EVALUATION_LOGIC_SYNTAX_INVALID"
    assert "compile" in result.message.lower()
    assert result.details


def test_accepts_valid_json_schema():
    result = validate_requirement(
        Requirement(
            engine=QualityEngine.schema,
            implementation='{"type":"object","required":["id"]}',
        )
    )

    assert result.valid is True
    assert result.code == "EVALUATION_LOGIC_VALID"


def test_rejects_invalid_json_schema_definition():
    result = validate_requirement(
        Requirement(
            engine=QualityEngine.schema,
            implementation='{"type":"not-a-json-schema-type"}',
        )
    )

    assert result.valid is False
    assert result.code == "EVALUATION_LOGIC_SYNTAX_INVALID"
    assert result.details


def test_accepts_valid_great_expectations_configuration():
    result = validate_requirement(
        Requirement(
            engine=QualityEngine.great_expectations,
            implementation="""
type: ExpectColumnValuesToBeBetween
kwargs:
  column: temperature
  min_value: 0
  max_value: 100
""",
        )
    )

    assert result.valid is True
    assert result.code == "EVALUATION_LOGIC_VALID"


def test_rejects_unknown_great_expectations_type():
    result = validate_requirement(
        Requirement(
            engine=QualityEngine.great_expectations,
            implementation="""
type: ExpectSomethingThatDoesNotExist
kwargs: {}
""",
        )
    )

    assert result.valid is False
    assert result.code == "EVALUATION_LOGIC_SYNTAX_INVALID"
    assert "unknown" in result.message.lower()


def test_validation_endpoint_returns_structured_result():
    client = TestClient(app)

    response = client.post(
        "/validate-requirement",
        json={"engine": "JQ", "implementation": ".items | | length"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == "EVALUATION_LOGIC_SYNTAX_INVALID"
    assert response.json()["engine"] == "JQ"
