"""
Run a template assistant proposal over its own examples.

A proposal's logic can compile – which is all validation checks – and still
fail on every document it meets: a jq result without ``details``, or a
``reduce`` that reads its accumulator instead of the input. So before the
author sees a proposal, it is rendered with the variable values the
assistant chose for its examples and run by DVA Processing over them: the
passing examples must pass, the failing ones fail, and none may error.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate as validate_json
from pydantic import BaseModel, Field

from .log import get_logger
from .models import _CAMEL, EvaluationMethod
from .templates import render_template
from .validation import ProcessingError, RequirementEvaluator

logger = get_logger(__name__)

# How much of an example document a problem report quotes.
_QUOTED_EXAMPLE_CHARS = 200


class SelfTestResult(BaseModel):
    """
    How a proposal fared against its own examples.

    ``skipped`` when there was no proposal to test, ``unavailable`` when DVA
    Processing could not be reached, so the proposal is untested.
    """

    model_config = _CAMEL

    status: Literal["passed", "failed", "unavailable", "skipped"]
    problems: list[str] = Field(default_factory=list)
    # 2 when the assistant was asked to correct a failed first attempt.
    attempts: int = 1


def _cases(examples: Any) -> list[tuple[bool, Any]]:
    """The examples as (should pass, document) pairs."""
    cases: list[tuple[bool, Any]] = []
    for key, expected in (("passing", True), ("failing", False)):
        value = (examples or {}).get(key) if isinstance(examples, dict) else None
        if value is None:
            continue
        items = value if isinstance(value, list) else [value]
        cases.extend((expected, item) for item in items)
    return cases


def _quote(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) > _QUOTED_EXAMPLE_CHARS:
        text = text[: _QUOTED_EXAMPLE_CHARS - 1] + "…"
    return text


async def self_test(
    reply: dict[str, Any], evaluator: RequirementEvaluator
) -> SelfTestResult:
    """Run ``reply``'s proposal over its examples; see the module docstring."""
    proposal = reply.get("proposal")
    if not proposal:
        return SelfTestResult(status="skipped")

    cases = _cases(reply.get("examples"))
    if not cases:
        return SelfTestResult(
            status="failed",
            problems=["No passing or failing examples were given to test it with."],
        )

    em = EvaluationMethod.model_validate(proposal["evaluationMethod"])
    model = reply.get("exampleModel") or {}
    try:
        validate_json(instance=model, schema=em.variable_schema)
    except JSONSchemaValidationError as exc:
        return SelfTestResult(
            status="failed",
            problems=[f"exampleModel does not match the variableSchema: {exc.message}"],
        )
    try:
        implementation = render_template(em.implementation_template, model)
    # chevron raises no one error type, so anything it raises is a failure
    # to render.
    except Exception as exc:
        return SelfTestResult(
            status="failed",
            problems=[f"implementationTemplate could not be rendered: {exc}"],
        )

    problems: list[str] = []
    for expected, data in cases:
        label = f"{'passing' if expected else 'failing'} example {_quote(data)}"
        try:
            code, body = await evaluator.evaluate(em.engine, implementation, data)
        except ProcessingError as exc:
            logger.warning("Could not self-test a template proposal", error=str(exc))
            return SelfTestResult(status="unavailable", problems=[str(exc)])
        body = body if isinstance(body, dict) else {}
        error = body.get("error") or (None if code == 200 else body.get("title"))
        if code != 200 or error:
            problems.append(
                f"The {label} could not be evaluated: {error or f'HTTP {code}'}"
            )
        elif body.get("success") is not expected:
            problems.append(
                f"The {label} should {'pass' if expected else 'fail'} but it "
                f"{'failed' if expected else 'passed'} (details: {body.get('details')})"
            )
    return SelfTestResult(status="failed" if problems else "passed", problems=problems)


def self_test_feedback(result: SelfTestResult) -> str:
    """The message asking the assistant to correct a proposal that failed."""
    listed = "\n".join(f"- {problem}" for problem in result.problems)
    return (
        "Your proposal failed its self-test: implementationTemplate, rendered "
        "with exampleModel, was run over your own examples and gave these "
        f"problems:\n{listed}\n"
        "Find the cause, fix implementationTemplate (and exampleModel or the "
        "examples, if they were what was wrong), and reply with the complete "
        "corrected JSON in the same shape as before."
    )
