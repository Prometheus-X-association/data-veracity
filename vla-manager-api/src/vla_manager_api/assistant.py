"""Small client and prompt builder for the VLA template assistant."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import cfg
from .models import TemplateNew


class AssistantUnavailable(RuntimeError):
    """The configured assistant service cannot be reached or is disabled."""


class AssistantResponseError(ValueError):
    """The assistant returned a response that is not valid JSON."""


def build_assistant_messages(
    message: str,
    templates: list[dict[str, Any]],
    conversation: list[dict[str, str]],
    current_template: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Build the bounded context sent to the configured chat service."""
    template_context = [
        {
            "name": item.get("name"),
            "description": item.get("description"),
            "engine": item.get("evaluationMethod", {}).get("engine"),
        }
        for item in templates
    ]
    system = (
        "You are the VLA template design assistant. Return JSON only with "
        "the shape {message, proposal, examples}. proposal must use the "
        "VLA Manager template fields name, description, criterionType, "
        "targetAspect, and evaluationMethod. evaluationMethod must contain "
        "engine, variableSchema, and implementationTemplate. Supported "
        "engines are SCHEMA, JQ, and GREAT_EXPECTATIONS. Never save data, "
        "invent unsupported engines, or claim that a generated proposal is "
        "validated. examples may contain passing and failing JSON samples. "
        f"Available templates: {json.dumps(template_context)}. "
        f"Current draft: {json.dumps(current_template or {})}."
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(conversation[-10:])
    messages.append({"role": "user", "content": message.strip()})
    return messages


def _completion_url() -> str:
    base = cfg.ai_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _complete_sync(messages: list[dict[str, str]]) -> str:
    if not cfg.ai_url or not cfg.ai_api_key or not cfg.ai_model:
        raise AssistantUnavailable("The template assistant is not configured.")

    body = json.dumps(
        {
            "model": cfg.ai_model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
    ).encode()
    request = Request(
        _completion_url(),
        data=body,
        headers={
            "Authorization": f"Bearer {cfg.ai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=cfg.ai_timeout_seconds) as response:
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise AssistantUnavailable(
            "The template assistant could not be reached."
        ) from exc

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AssistantResponseError(
            "The assistant response had an unexpected shape."
        ) from exc
    if not isinstance(content, str):
        raise AssistantResponseError("The assistant response was not text.")
    return content


async def complete_assistant(messages: list[dict[str, str]]) -> str:
    """Call the configured service without blocking the API event loop."""
    return await asyncio.to_thread(_complete_sync, messages)


def parse_assistant_response(content: str) -> dict[str, Any]:
    """Parse model JSON and require the top-level fields used by the UI."""
    try:
        response = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AssistantResponseError("The assistant returned invalid JSON.") from exc
    if not isinstance(response, dict) or not isinstance(response.get("message"), str):
        raise AssistantResponseError("The assistant response is missing its message.")
    proposal = response.get("proposal")
    if proposal is not None and not isinstance(proposal, dict):
        raise AssistantResponseError("The assistant proposal is not an object.")
    if proposal is not None:
        try:
            proposal = TemplateNew.model_validate(proposal).model_dump(
                by_alias=True, exclude_none=True
            )
        except ValueError as exc:
            raise AssistantResponseError(
                "The assistant proposal does not match the template schema."
            ) from exc
    examples = response.get("examples")
    if examples is not None and not isinstance(examples, dict):
        raise AssistantResponseError("The assistant examples are not an object.")
    return {"message": response["message"], "proposal": proposal, "examples": examples}
