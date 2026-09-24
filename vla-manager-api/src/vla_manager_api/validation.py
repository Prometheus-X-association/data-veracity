"""
Client for the DVA Processing validation endpoint, and the requirement check
built on it.

The client is built once during ``lifespan`` and read off ``app.state``,
like the repositories; tests swap it through
``app.dependency_overrides[get_requirement_validator]``.
:func:`check_requirement` is shared by ``POST /template/{id}/validate`` and
``POST /vla/from-templates``, so a requirement the author was told is valid
is exactly one the VLA can be created from.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Optional, Protocol

import httpx2
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate as validate_json

from .log import get_logger
from .models import (
    EvaluationMethod,
    QualityEngine,
    TemplateValidationResult,
    ValidationFailureReason,
)
from .templates import render_template

logger = get_logger(__name__)

# DVA Processing is a sibling service on the same network, and compiling an
# expression is not slow, so a call unanswered by now is not going to be.
TIMEOUT_SECONDS = 10

# The required fields of processing's `RequirementValidationResult`
# (docs/spec/dva-processing.yaml): `{valid, reason?, engine, details?}`.
_REQUIRED_FIELDS = frozenset({"valid", "engine"})

# Processing's `reason`, which it gives only when `valid` is false, as the
# reason this service reports; both sides use the same two values.
_REASONS = {reason.value: reason for reason in ValidationFailureReason}


class ProcessingError(Exception):
    """DVA Processing could not be reached, or answered unusably."""


class RequirementValidator(Protocol):
    """Checks that a requirement's evaluation logic compiles."""

    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult: ...


def _reason(answer: dict[str, Any]) -> Optional[ValidationFailureReason]:
    """Read processing's ``reason`` as the reason this service reports."""
    if answer["valid"]:
        return None
    try:
        return _REASONS[answer.get("reason")]
    except KeyError as e:
        # A failure we cannot name is not one to pass off as valid, and the
        # spec requires a reason whenever `valid` is false.
        raise ProcessingError(
            f"DVA Processing reported an invalid result with unknown reason "
            f"{answer.get('reason')}"
        ) from e


def _to_result(
    engine: QualityEngine, implementation: str, answer: dict[str, Any]
) -> TemplateValidationResult:
    """Map processing's answer onto the result this service returns."""
    # `engine` is not taken from the answer: the engine asked about is the
    # one reported.
    return TemplateValidationResult(
        valid=answer["valid"],
        reason=_reason(answer),
        engine=engine,
        details=answer.get("details"),
        implementation=implementation,
    )


class ProcessingRequirementValidator:
    """A :class:`RequirementValidator` backed by the DVA Processing service."""

    def __init__(
        self, processing_url: str, client: httpx2.AsyncClient | None = None
    ) -> None:
        self._url = f"{processing_url.rstrip('/')}/validate-requirement"
        # Injectable so tests can answer over a stubbed transport; in
        # production this owns the connection pool it opens here.
        self._client = client or httpx2.AsyncClient(timeout=TIMEOUT_SECONDS)

    async def aclose(self) -> None:
        """Release the pooled connections. Called once, at shutdown."""
        await self._client.aclose()

    async def __aenter__(self) -> ProcessingRequirementValidator:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult:
        """Have processing compile ``implementation`` and report its verdict."""
        body = {"engine": engine.value, "implementation": implementation}
        logger.debug(
            "Validating rendered logic with DVA Processing", url=self._url, body=body
        )
        try:
            response = await self._client.post(self._url, json=body)
        except httpx2.HTTPError as e:
            raise ProcessingError(f"Request to DVA Processing failed: {e}") from e

        logger.debug(
            "DVA Processing answered",
            url=self._url,
            status=response.status_code,
            body=response.text,
        )
        try:
            response.raise_for_status()
            answer = response.json()
        except (httpx2.HTTPError, ValueError) as e:
            raise ProcessingError(f"Unusable DVA Processing response: {e}") from e

        # Checked here so the mapping below can read the fields it needs
        # without a missing key reaching the route as a 500.
        missing = _REQUIRED_FIELDS - answer.keys()
        if missing:
            raise ProcessingError(
                f"DVA Processing answered without {', '.join(sorted(missing))}"
            )
        return _to_result(engine, implementation, answer)


async def check_requirement(
    em: EvaluationMethod, model: dict[str, Any], validator: RequirementValidator
) -> TemplateValidationResult:
    """
    Check ``model`` against a template's evaluation method, end to end.

    The input must match the variable schema, the template must render with
    it, and processing must accept the rendered logic. Every way this can go
    wrong is reported as a verdict rather than raised, so a caller can
    decide whether a failure is the author's to fix or an outage. A passing
    verdict always carries the rendered ``implementation``.
    """
    try:
        validate_json(instance=model, schema=em.variable_schema)
    except JSONSchemaValidationError as exc:
        return TemplateValidationResult(
            valid=False,
            reason=ValidationFailureReason.invalid_implementation,
            engine=em.engine,
            details=(
                f"The template input does not match its variable schema.\n{exc.message}"
            ),
        )

    try:
        rendered = render_template(em.implementation_template, model)
    # chevron raises no one error type, so anything it raises is a failure
    # to render.
    except Exception as exc:
        return TemplateValidationResult(
            valid=False,
            reason=ValidationFailureReason.invalid_implementation,
            engine=em.engine,
            details=f"The template could not be rendered.\n{exc}",
        )

    try:
        result = await validator.validate(em.engine, rendered)
    except ProcessingError as exc:
        logger.warning("Could not validate rendered logic", error=str(exc))
        return TemplateValidationResult(
            valid=False,
            reason=ValidationFailureReason.unavailable_engine,
            engine=em.engine,
            details=f"The evaluation service is unavailable.\n{exc}",
            implementation=rendered,
        )
    if result.implementation is None:
        result = result.model_copy(update={"implementation": rendered})
    return result
