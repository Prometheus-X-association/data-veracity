"""
Error responses shaped like the spec's ``Error`` schema.

``docs/spec/vla-manager-api.yaml`` declares every error response as
``{type, title}``. FastAPI's default handler instead wraps whatever it is
given under a ``detail`` key, so this module supplies both halves: a
:func:`http_error` helper for raise sites, and the handler that renders
the payload at the top level.

Request-body validation is deliberately left alone — those stay as
FastAPI's own ``422`` with its ``{"detail": [...]}`` array, which the
spec documents separately.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from .models import ErrDTO


def http_error(status_code: int, title: str, type: str | None = None) -> HTTPException:
    """
    Build an ``HTTPException`` whose detail is an ``Error`` payload.

    ``type`` defaults to the HTTP status constant (``404`` →
    ``NOT_FOUND``), which keeps the raise sites to a single line.
    """
    return HTTPException(
        status_code,
        detail=ErrDTO(
            type=type or HTTPStatus(status_code).name, title=title
        ).model_dump(),
    )


def _as_problem(status_code: int, detail: object) -> ErrDTO:
    """Coerce an exception detail into the spec's ``Error`` shape."""
    if isinstance(detail, dict) and {"type", "title"} <= detail.keys():
        return ErrDTO.model_validate(detail)

    status = HTTPStatus(status_code)
    title = detail if isinstance(detail, str) and detail else status.phrase
    return ErrDTO(type=status.name, title=str(title))


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Render ``HTTPException`` as ``{type, title}`` rather than ``{detail}``."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_as_problem(exc.status_code, exc.detail).model_dump(),
        headers=getattr(exc, "headers", None),
    )
