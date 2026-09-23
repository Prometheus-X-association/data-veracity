"""Small client and prompt builder for the VLA template assistant."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from structlog.contextvars import bound_contextvars

from .config import cfg
from .log import get_logger
from .models import TemplateNew

logger = get_logger(__name__)

_DEFAULT_URLS = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
_DEFAULT_MODELS = {"gemini": "gemini-3.1-flash-lite"}

# Request headers that carry credentials; logged as present, never by value.
_SECRET_HEADERS = frozenset({"authorization", "x-api-key", "x-goog-api-key"})


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
        "engines are SCHEMA, JQ, and GREAT_EXPECTATIONS. criterionType must "
        "be one of VALID_INVALID, IN_RANGE, GREATER_THAN, LESS_THAN. "
        "targetAspect must be one of SYNTAX, TIMELINESS, ACCURACY, "
        "COMPLETENESS, CONSISTENCY. Never save data, invent unsupported "
        "engines, or claim that a generated proposal is validated. examples "
        'must be an object with "passing" and "failing" values. Each value '
        "should contain at least two representative examples when possible; "
        "use an array for multiple examples, never a top-level array. Return "
        "plain JSON without markdown fences. The implementationTemplate is "
        "executed directly by the selected evaluator, so it must be code, "
        "not an explanation. SCHEMA implementationTemplate must be a string "
        "containing valid JSON Schema JSON, for example "
        '\'{"type":"object","properties":{}}\'. '
        "JQ implementationTemplate must be the executable jq expression "
        "that returns an object with a boolean success field and optional "
        "details string. GREAT_EXPECTATIONS implementationTemplate must be "
        "a string containing valid YAML expectation configuration with type, "
        "kwargs, and optional meta fields. Never put prose such as 'check "
        "that...' in implementationTemplate. "
        f"Available templates: {json.dumps(template_context)}. "
        f"Current draft: {json.dumps(current_template or {})}."
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(conversation[-10:])
    messages.append({"role": "user", "content": message.strip()})
    return messages


def _provider_config() -> tuple[str, str, str, str]:
    provider = cfg.ai_provider
    if provider not in _DEFAULT_URLS:
        raise AssistantUnavailable(
            "The configured assistant provider is not supported."
        )

    api_key = cfg.ai_api_key.strip()
    base_url = cfg.ai_url.strip() or _DEFAULT_URLS[provider]
    model = cfg.ai_model.strip() or _DEFAULT_MODELS.get(provider, "")
    if not api_key or not model:
        logger.warning(
            "Template assistant is not configured",
            provider=provider,
            url=base_url,
            has_api_key=bool(api_key),
            model=model or None,
        )
        raise AssistantUnavailable("The template assistant is not configured.")
    return provider, base_url, model, api_key


def _completion_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _messages_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/messages"):
        return base
    return f"{base}/messages"


def _redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        name: "<redacted>" if name.lower() in _SECRET_HEADERS else value
        for name, value in headers.items()
    }


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 1)


def _decode_body(raw: bytes) -> Any:
    """The body as JSON if it parses, else as text, for logging."""
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _post_json(
    url: str,
    body: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any]:
    headers = {**headers, "Content-Type": "application/json"}
    request = Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    logger.debug(
        "Sending request to AI endpoint",
        method="POST",
        url=url,
        headers=_redact_headers(headers),
        body=body,
        timeout_seconds=cfg.ai_timeout_seconds,
    )
    started = perf_counter()
    try:
        with urlopen(request, timeout=cfg.ai_timeout_seconds) as response:
            status = response.status
            response_headers = dict(response.headers.items())
            raw = response.read()
    except HTTPError as exc:
        # Providers explain rejections (bad key, unknown model, rate limit)
        # in the body, so that is worth keeping even outside debug.
        try:
            error_body = _decode_body(exc.read())
        except OSError:
            error_body = None
        logger.warning(
            "AI endpoint answered with an error",
            url=url,
            status=exc.code,
            reason=exc.reason,
            elapsed_ms=_elapsed_ms(started),
            headers=dict(exc.headers.items()) if exc.headers else None,
            body=error_body,
        )
        raise AssistantUnavailable(
            "The template assistant could not be reached."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning(
            "AI endpoint could not be reached",
            url=url,
            elapsed_ms=_elapsed_ms(started),
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise AssistantUnavailable(
            "The template assistant could not be reached."
        ) from exc

    elapsed_ms = _elapsed_ms(started)
    logger.debug(
        "Received response from AI endpoint",
        url=url,
        status=status,
        elapsed_ms=elapsed_ms,
        headers=response_headers,
        body=_decode_body(raw),
    )
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning(
            "AI endpoint returned invalid JSON",
            url=url,
            status=status,
            body=raw.decode("utf-8", errors="replace"),
        )
        raise AssistantResponseError("The assistant returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        logger.warning(
            "AI endpoint returned a non-object", url=url, status=status, body=payload
        )
        raise AssistantResponseError("The assistant response had an unexpected shape.")
    logger.info(
        "AI endpoint replied",
        url=url,
        status=status,
        elapsed_ms=elapsed_ms,
        usage=payload.get("usage"),
    )
    return payload


def _complete_openai_compatible(
    messages: list[dict[str, str]],
    base_url: str,
    model: str,
    api_key: str,
    provider: str,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    if provider == "gemini":
        headers["x-goog-api-client"] = "prometheus-x-data-veracity/0.1"
    payload = _post_json(
        _completion_url(base_url),
        {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        headers,
    )

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AssistantResponseError(
            "The assistant response had an unexpected shape."
        ) from exc
    if not isinstance(content, str):
        raise AssistantResponseError("The assistant response was not text.")
    return content


def _complete_anthropic(
    messages: list[dict[str, str]],
    base_url: str,
    model: str,
    api_key: str,
) -> str:
    system_messages = [item["content"] for item in messages if item["role"] == "system"]
    chat_messages = [item for item in messages if item["role"] in {"user", "assistant"}]
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": 2048,
        "temperature": 0.2,
        "messages": chat_messages,
    }
    if system_messages:
        body["system"] = "\n\n".join(system_messages)
    payload = _post_json(
        _messages_url(base_url),
        body,
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    blocks = payload.get("content")
    if not isinstance(blocks, list):
        raise AssistantResponseError("The assistant response had an unexpected shape.")
    content = "".join(
        block["text"]
        for block in blocks
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    )
    if not content:
        raise AssistantResponseError("The assistant response was not text.")
    return content


def _complete_sync(messages: list[dict[str, str]]) -> str:
    provider, base_url, model, api_key = _provider_config()
    # Scoped to this call, so every event it logs says which service it was.
    with bound_contextvars(ai_provider=provider, ai_model=model):
        if provider == "anthropic":
            content = _complete_anthropic(messages, base_url, model, api_key)
        else:
            content = _complete_openai_compatible(
                messages, base_url, model, api_key, provider
            )
        logger.debug("Extracted assistant reply", content=content)
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
        _validate_implementation_template(proposal)
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


def _validate_implementation_template(proposal: dict[str, Any]) -> None:
    """Reject assistant prose before it reaches the template editor.

    Templates may contain Mustache placeholders, so static validation is only
    applied when the implementation is self-contained. The selected evaluator
    will validate rendered templates again when they are used.
    """
    evaluation_method = proposal.get("evaluationMethod")
    if not isinstance(evaluation_method, dict):
        return

    engine = evaluation_method.get("engine")
    implementation = evaluation_method.get("implementationTemplate")
    if not isinstance(implementation, str) or not implementation.strip():
        return
    if "{{" in implementation or "}}" in implementation:
        return

    if engine == "SCHEMA":
        try:
            parsed = json.loads(implementation)
        except json.JSONDecodeError as exc:
            raise AssistantResponseError(
                "The assistant returned a SCHEMA implementation that is not valid JSON Schema JSON."
            ) from exc
        if not isinstance(parsed, (dict, bool)):
            raise AssistantResponseError(
                "The assistant returned a SCHEMA implementation that is not a JSON Schema object."
            )
