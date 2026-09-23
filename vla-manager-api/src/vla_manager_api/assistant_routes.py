"""HTTP endpoint for the VLA template design assistant."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator

from .assistant import (
    AssistantResponseError,
    AssistantUnavailable,
    build_assistant_messages,
    complete_assistant,
    parse_assistant_response,
)
from .dependencies import get_template_repo
from .errors import http_error
from .log import get_logger
from .models import _CAMEL_OPEN
from .template_repo import TemplateRepo

logger = get_logger(__name__)

router = APIRouter()


class AssistantRequest(BaseModel):
    model_config = _CAMEL_OPEN

    message: str = Field(min_length=1, max_length=4000)
    conversation: list[dict[str, str]] = Field(default_factory=list, max_length=20)
    current_template: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must contain text")
        return value


class AssistantReply(BaseModel):
    model_config = _CAMEL_OPEN

    message: str
    proposal: dict[str, Any] | None = None
    examples: dict[str, Any] | None = None


@router.post("/assistant/template", response_model=AssistantReply)
async def assist_template(
    request: AssistantRequest,
    repo: TemplateRepo = Depends(get_template_repo),
) -> AssistantReply:
    try:
        templates = await repo.all()
        messages = build_assistant_messages(
            request.message,
            templates,
            request.conversation,
            request.current_template,
        )
        content = await complete_assistant(messages)
        reply = AssistantReply.model_validate(parse_assistant_response(content))
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

    proposal = reply.proposal or {}
    logger.info(
        "Template assistant replied",
        has_proposal=reply.proposal is not None,
        engine=proposal.get("evaluationMethod", {}).get("engine"),
        has_examples=reply.examples is not None,
    )
    return reply
