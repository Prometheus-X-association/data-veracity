"""
Logging setup for the VLA Manager API.

Everything is rendered by structlog: the service's own events, and – through
:class:`structlog.stdlib.ProcessorFormatter` on the root handler – the records
uvicorn, httpx2 and asyncpg emit through the standard library.  Output is
human-readable when stderr is a TTY and one JSON object per line otherwise,
unless ``VLA_MANAGER_API_LOG_FORMAT`` says which.

Each HTTP request is given a ``request_id`` (the caller's ``X-Request-ID``, or
a fresh one), bound for the request's duration so every event it causes –
including the outgoing calls to the assistant service – carries it.
"""

from __future__ import annotations

import logging
from sys import stderr
from typing import Any
from uuid import uuid4

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from structlog import make_filtering_bound_logger
from structlog.contextvars import bound_contextvars, merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    dict_tracebacks,
)
from structlog.stdlib import (
    LoggerFactory,
    ProcessorFormatter,
    add_log_level,
    add_logger_name,
)
from structlog.typing import EventDict, FilteringBoundLogger, Processor, WrappedLogger

from .config import cfg

REQUEST_ID_HEADER = b"x-request-id"

# Libraries whose debug output is connection-level chatter rather than
# anything about this service; they stay at INFO even when we go to DEBUG.
_QUIET_LOGGERS = ("httpcore2", "asyncio")


class _StructlogHandler(logging.StreamHandler):
    """Marks the root handler as ours, so reconfiguring replaces only it."""


def _uvicorn_access_fields(
    _logger: WrappedLogger, _method: str, event_dict: EventDict
) -> EventDict:
    """Lift uvicorn's access-log arguments into fields of their own.

    ``ProcessorFormatter`` hands a foreign record's arguments over as
    ``positional_args``; they are dropped for every other record, whose
    message already has them interpolated.
    """
    args = event_dict.pop("positional_args", None)
    record = event_dict.get("_record")
    if (
        record is not None
        and record.name == "uvicorn.access"
        and isinstance(args, tuple)
        and len(args) == 5
    ):
        client, method, path, http_version, status = args
        event_dict.update(
            client=client,
            method=method,
            path=path,
            http_version=http_version,
            status=status,
        )
    return event_dict


def _use_json() -> bool:
    if cfg.log_format == "auto":
        return not stderr.isatty()
    return cfg.log_format == "json"


def setup_logging() -> None:
    """Configure structlog and the stdlib root logger. Called from the app
    factory, and safe to call again."""
    level = logging.getLevelName(cfg.log_level.upper())
    shared: list[Processor] = [
        merge_contextvars,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso", utc=True),
        StackInfoRenderer(),
    ]
    renderer: list[Processor] = (
        [dict_tracebacks, JSONRenderer()] if _use_json() else [ConsoleRenderer()]
    )

    structlog.configure(
        processors=[*shared, ProcessorFormatter.wrap_for_formatter],
        logger_factory=LoggerFactory(),
        wrapper_class=make_filtering_bound_logger(level),
        context_class=dict,
    )

    handler = _StructlogHandler(stderr)
    handler.setFormatter(
        ProcessorFormatter(
            foreign_pre_chain=[*shared, _uvicorn_access_fields],
            pass_foreign_args=True,
            processors=[ProcessorFormatter.remove_processors_meta, *renderer],
        )
    )
    root = logging.getLogger()
    # Leave other handlers (eg pytest's capture) alone.
    root.handlers = [h for h in root.handlers if not isinstance(h, _StructlogHandler)]
    root.addHandler(handler)
    root.setLevel(level)
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(max(level, logging.INFO))


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Return the application logger, named after ``name`` if given."""
    return structlog.get_logger(name)


class RequestContextMiddleware:
    """
    Bind a ``request_id`` to every event logged while serving a request.

    A plain ASGI middleware rather than Starlette's ``BaseHTTPMiddleware``,
    so the endpoint runs in this context and not a copy of it.  The ID is
    echoed back in the ``X-Request-ID`` response header.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers: dict[bytes, bytes] = dict(scope["headers"])
        request_id = (
            headers.get(REQUEST_ID_HEADER, b"").decode("latin-1") or uuid4().hex
        )

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers: list[Any] = list(message.get("headers", []))
                response_headers.append(
                    (REQUEST_ID_HEADER, request_id.encode("latin-1"))
                )
                message = {**message, "headers": response_headers}
            await send(message)

        with bound_contextvars(request_id=request_id):
            await self.app(scope, receive, send_with_id)
