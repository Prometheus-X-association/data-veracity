"""HTTP endpoint for the VLA template design assistant."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator

from .assistant import (
    AssistantResponseError,
    AssistantUnavailable,
    build_assistant_messages,
    build_vla_assistant_messages,
    complete_assistant,
    parse_assistant_response,
    parse_vla_assistant_response,
)
from .dependencies import get_requirement_evaluator, get_template_repo
from .errors import http_error
from .log import get_logger
from .models import _CAMEL
from .template_repo import TemplateRepo
from .template_self_test import SelfTestResult, self_test, self_test_feedback
from .validation import RequirementEvaluator

logger = get_logger(__name__)

router = APIRouter()


class ConversationTurn(BaseModel):
    """An earlier chat turn replayed to the model.

    Only ``user`` and ``assistant`` turns are accepted: the system prompt is
    the server's alone, and a client-supplied ``system`` turn would be merged
    into it by the Anthropic path.
    """

    model_config = _CAMEL

    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class AssistantRequest(BaseModel):
    model_config = _CAMEL

    message: str = Field(min_length=1, max_length=4000)
    conversation: list[ConversationTurn] = Field(default_factory=list, max_length=20)
    current_template: dict[str, Any] | None = None
    # The assistant's last proposal, so a follow-up can adjust it; the
    # conversation only carries the assistant's prose.
    proposal: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must contain text")
        return value


class AssistantReply(BaseModel):
    model_config = _CAMEL

    message: str
    proposal: dict[str, Any] | None = None
    examples: dict[str, Any] | None = None
    # The variable values the examples were written for.
    example_model: dict[str, Any] | None = None
    # How the proposal fared when run over its own examples.
    self_test: SelfTestResult | None = None


class BuilderContext(BaseModel):
    model_config = _CAMEL

    metadata: dict[str, Any] = Field(default_factory=dict)
    sample_data: Any | None = None
    selected_path: str | None = None
    fragments: list[dict[str, Any]] = Field(default_factory=list)
    # The assistant's previous draft, so a recheck can complete it rather
    # than start over; the conversation only carries its prose.
    draft: dict[str, Any] | None = None


class AssistantVLARequest(BaseModel):
    model_config = _CAMEL

    message: str = Field(min_length=1, max_length=4000)
    conversation: list[ConversationTurn] = Field(default_factory=list, max_length=20)
    builder_context: BuilderContext = Field(default_factory=BuilderContext)

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must contain text")
        return value


class VLAAssistantRequirement(BaseModel):
    model_config = _CAMEL

    template_id: str
    model: dict[str, Any]
    reason: str


class AssistantVLAReply(BaseModel):
    model_config = _CAMEL

    message: str
    metadata: dict[str, Any] | None = None
    requirements: list[VLAAssistantRequirement] = Field(default_factory=list)
    missing_templates: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/assistant/template", response_model=AssistantReply)
async def assist_template(
    request: AssistantRequest,
    repo: TemplateRepo = Depends(get_template_repo),
    evaluator: RequirementEvaluator = Depends(get_requirement_evaluator),
) -> AssistantReply:
    try:
        templates = await repo.all()
        messages = build_assistant_messages(
            request.message,
            templates,
            [turn.model_dump() for turn in request.conversation],
            request.current_template,
            request.proposal,
        )
        content = await complete_assistant(messages)
        parsed = parse_assistant_response(content)
    except AssistantUnavailable as exc:
        logger.warning("Template assistant unavailable", error=str(exc))
        raise http_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(exc),
            type="ASSISTANT_UNAVAILABLE",
        ) from exc
    except AssistantResponseError as exc:
        logger.warning(
            "Template assistant response rejected",
            error=str(exc),
            cause=str(exc.__cause__) if exc.__cause__ else None,
        )
        raise http_error(
            status.HTTP_502_BAD_GATEWAY,
            str(exc),
            type="ASSISTANT_INVALID_RESPONSE",
        ) from exc

    parsed, result = await _self_tested(parsed, content, messages, evaluator)
    reply = AssistantReply.model_validate({**parsed, "selfTest": result})

    proposal = reply.proposal or {}
    logger.info(
        "Template assistant replied",
        has_proposal=reply.proposal is not None,
        engine=proposal.get("evaluationMethod", {}).get("engine"),
        has_examples=reply.examples is not None,
        self_test=result.status,
        attempts=result.attempts,
    )
    return reply


async def _self_tested(
    parsed: dict[str, Any],
    content: str,
    messages: list[dict[str, str]],
    evaluator: RequirementEvaluator,
) -> tuple[dict[str, Any], SelfTestResult]:
    """
    Run the proposal over its examples, and give the assistant one chance
    to correct a proposal that fails, with the problems it caused.

    A correction that cannot be had – the assistant unreachable, its answer
    unusable, or no proposal in it – leaves the first proposal standing with
    its failed result, so the author still sees what went wrong.
    """
    result = await self_test(parsed, evaluator)
    if result.status != "failed":
        return parsed, result

    logger.info(
        "Template proposal failed its self-test; asking for a correction",
        problems=result.problems,
    )
    retry = [
        *messages,
        {"role": "assistant", "content": content},
        {"role": "user", "content": self_test_feedback(result)},
    ]
    try:
        corrected = parse_assistant_response(await complete_assistant(retry))
    except (AssistantUnavailable, AssistantResponseError) as exc:
        logger.warning("Could not get a corrected proposal", error=str(exc))
        return parsed, result.model_copy(update={"attempts": 2})
    if not corrected.get("proposal"):
        return parsed, result.model_copy(update={"attempts": 2})
    corrected_result = await self_test(corrected, evaluator)
    return corrected, corrected_result.model_copy(update={"attempts": 2})


@router.post("/assistant/vla", response_model=AssistantVLAReply)
async def assist_vla(
    request: AssistantVLARequest,
    repo: TemplateRepo = Depends(get_template_repo),
) -> AssistantVLAReply:
    try:
        templates = await repo.all()
        messages = build_vla_assistant_messages(
            request.message,
            request.builder_context.model_dump(by_alias=True, mode="json"),
            templates,
            [turn.model_dump() for turn in request.conversation],
        )
        content = await complete_assistant(messages)
        catalog_ids = {item.id for item in templates}
        parsed = parse_vla_assistant_response(content, catalog_ids)
        reply = AssistantVLAReply.model_validate(parsed)
    except AssistantUnavailable as exc:
        logger.warning("VLA assistant unavailable", error=str(exc))
        raise http_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(exc),
            type="ASSISTANT_UNAVAILABLE",
        ) from exc
    except AssistantResponseError as exc:
        logger.warning(
            "VLA assistant response rejected",
            error=str(exc),
            cause=str(exc.__cause__) if exc.__cause__ else None,
        )
        raise http_error(
            status.HTTP_502_BAD_GATEWAY,
            str(exc),
            type="ASSISTANT_INVALID_RESPONSE",
        ) from exc

    logger.info(
        "VLA assistant replied",
        requirements=len(reply.requirements),
        missing_templates=len(reply.missing_templates),
        has_metadata=reply.metadata is not None,
    )
    return reply
