"""
Logging setup for the DVA VC Manager.

structlog renders human-readable output when stderr is a TTY and JSON otherwise.
"""

from __future__ import annotations

from sys import stderr

import structlog
from structlog import make_filtering_bound_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, StackInfoRenderer, TimeStamper
from structlog.stdlib import add_log_level
from structlog.typing import FilteringBoundLogger

from .config import cfg


def setup_logging() -> None:
    """Configure structlog. Called once from the app factory."""
    shared = [add_log_level, StackInfoRenderer(), TimeStamper(fmt="iso")]
    processors = shared + ([ConsoleRenderer()] if stderr.isatty() else [JSONRenderer()])
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(cfg.log_level),
    )


def get_logger() -> FilteringBoundLogger:
    """Return the application logger."""
    return structlog.get_logger()
