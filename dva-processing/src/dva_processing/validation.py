"""
Static validation of a requirement's evaluation logic.

Compiles – but never runs – the implementation of an ODCS ``DataQuality``
entry, so the VLA Manager UI can tell an author that an expression is
malformed before there is any data to evaluate it against.  Every outcome
is a :class:`RequirementValidationResult`.
"""

from open_data_contract_standard.model import DataQuality

from .engines import great_expectations as ge
from .engines import jq
from .engines import json_schema as schema
from .eval import parse_engine
from .log import get_logger
from .model import (
    QualityEngine,
    RequirementValidationFailureReason,
    RequirementValidationResult,
)

logger = get_logger()


def _valid(engine: QualityEngine) -> RequirementValidationResult:
    return RequirementValidationResult(
        valid=True,
        engine=engine,
        details="The evaluation logic is valid.",
    )


def _invalid(
    engine: QualityEngine, message: str, details: str
) -> RequirementValidationResult:
    return RequirementValidationResult(
        valid=False,
        engine=engine,
        reason=RequirementValidationFailureReason.invalid_implementation,
        details=details,
    )


def _unavailable(
    engine: QualityEngine, error: Exception
) -> RequirementValidationResult:
    return RequirementValidationResult(
        valid=False,
        engine=engine,
        reason=RequirementValidationFailureReason.unavailable_engine,
        details=f"The evaluation engine is unavailable.\n{error}",
    )


def _compile(engine: QualityEngine, implementation: str) -> None:
    """Compile ``implementation`` for ``engine``, raising if it is malformed."""
    match engine:
        case QualityEngine.jq:
            jq.compile_expression(implementation)
        case QualityEngine.schema:
            schema.check_schema(implementation)
        case QualityEngine.great_expectations:
            ge.build_expectation(ge.parse_implementation(implementation))


def validate_requirement(requirement: DataQuality) -> RequirementValidationResult:
    """Report whether ``requirement`` carries evaluation logic that compiles."""
    engine = parse_engine(requirement.engine)
    implementation = requirement.implementation

    # ODCS types `implementation` as a string, an object or nothing at
    # all; the engines all read it as source text, so the other two are
    # malformed logic rather than something to validate.
    if not isinstance(implementation, str) or not implementation.strip():
        return _invalid(
            engine,
            "The evaluation implementation is empty.",
            "A requirement must carry its evaluation logic as a string.",
        )

    try:
        _compile(engine, implementation)
    except (ImportError, OSError) as error:
        logger.warning("Evaluation engine unavailable", engine=engine, error=error)
        return _unavailable(engine, error)
    except ge.UnknownExpectationError as error:
        return _invalid(engine, str(error), str(error))
    except Exception as error:
        return _invalid(
            engine,
            f"The {engine} implementation could not be compiled.",
            str(error),
        )

    return _valid(engine)
