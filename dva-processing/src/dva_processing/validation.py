import html
import json

import jq as jq_library
from great_expectations import expectations
from jsonschema.validators import validator_for

from .engines import great_expectations as ge
from .model import (
    QualityEngine,
    Requirement,
    RequirementValidationResult,
    RequirementValidationStatus,
)


def _valid(requirement: Requirement) -> RequirementValidationResult:
    return RequirementValidationResult(
        valid=True,
        status=RequirementValidationStatus.valid,
        code="EVALUATION_LOGIC_VALID",
        engine=requirement.engine,
        message="The evaluation logic is valid.",
    )


def _invalid(
    requirement: Requirement, message: str, error: Exception
) -> RequirementValidationResult:
    return RequirementValidationResult(
        valid=False,
        status=RequirementValidationStatus.invalid,
        code="EVALUATION_LOGIC_SYNTAX_INVALID",
        engine=requirement.engine,
        message=message,
        details=str(error),
    )


def _validate_jq(requirement: Requirement) -> None:
    jq_library.compile(requirement.implementation)


def _validate_schema(requirement: Requirement) -> None:
    schema = json.loads(html.unescape(requirement.implementation))
    validator_for(schema).check_schema(schema)


def _validate_great_expectations(requirement: Requirement) -> None:
    params = ge.parse_implementation(requirement.implementation)
    expectation_type = getattr(expectations, params.type, None)
    if expectation_type is None:
        raise ValueError(f"Unknown Great Expectations type: {params.type}")
    expectation_type(**params.kwargs)


def validate_requirement(requirement: Requirement) -> RequirementValidationResult:
    try:
        match requirement.engine:
            case QualityEngine.jq:
                _validate_jq(requirement)
            case QualityEngine.schema:
                _validate_schema(requirement)
            case QualityEngine.great_expectations:
                _validate_great_expectations(requirement)
        return _valid(requirement)
    except (ImportError, OSError) as error:
        return RequirementValidationResult(
            valid=False,
            status=RequirementValidationStatus.unavailable,
            code="EVALUATION_ENGINE_UNAVAILABLE",
            engine=requirement.engine,
            message="The evaluation engine is unavailable.",
            details=str(error),
        )
    except Exception as error:
        engine_name = requirement.engine.value.replace("_", " ")
        message = (
            str(error)
            if str(error).startswith("Unknown Great Expectations type")
            else f"The {engine_name} implementation could not be compiled."
        )
        return _invalid(
            requirement,
            message,
            error,
        )
