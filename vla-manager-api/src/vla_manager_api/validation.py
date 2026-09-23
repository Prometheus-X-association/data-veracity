"""
Client for the DVA Processing validation endpoint.

The client is built once during ``lifespan`` and read off ``app.state``,
like the repositories; tests swap it through
``app.dependency_overrides[get_requirement_validator]``.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Optional, Protocol

import httpx2

from .log import get_logger
from .models import (
    QualityEngine,
    TemplateValidationResult,
    ValidationFailureReason,
)

logger = get_logger(__name__)

# DVA Processing is a sibling service on the same network, and compiling an
# expression is not slow, so a call unanswered by now is not going to be.
TIMEOUT_SECONDS = 10

# Of processing's `RequirementValidationResult`; `engine` is not among them,
# because the engine we asked about is the one we report.
_REQUIRED_FIELDS = frozenset({"valid", "status", "message"})

# Processing's `status` narrowed to the two reasons this service reports.
# `VALID` is absent: a pass carries no reason at all.
_REASONS = {
    "INVALID": ValidationFailureReason.invalid_implementation,
    "UNAVAILABLE": ValidationFailureReason.unavailable_engine,
}


class ProcessingError(Exception):
    """DVA Processing could not be reached, or answered unusably."""


class RequirementValidator(Protocol):
    """Checks that a requirement's evaluation logic compiles."""

    async def validate(
        self, engine: QualityEngine, implementation: str
    ) -> TemplateValidationResult: ...


def _reason(answer: dict[str, Any]) -> Optional[ValidationFailureReason]:
    """Narrow processing's ``status`` to the reason this service reports."""
    if answer["valid"]:
        return None
    try:
        return _REASONS[answer["status"]]
    except KeyError as e:
        # A failure we cannot name is not one to pass off as valid, and the
        # spec requires a reason whenever `valid` is false.
        raise ProcessingError(
            f"DVA Processing reported unknown status {answer['status']}"
        ) from e


def _to_result(
    engine: QualityEngine, implementation: str, answer: dict[str, Any]
) -> TemplateValidationResult:
    """Map processing's answer onto the result this service returns."""
    details = answer["message"]
    if answer.get("details"):
        details = f"{details}\n{answer['details']}"

    return TemplateValidationResult(
        valid=answer["valid"],
        reason=_reason(answer),
        engine=engine,
        details=details,
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
