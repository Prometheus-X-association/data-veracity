"""
Template rendering for VLA Templates.

Uses Handlebars-compatible ``{{var}}`` syntax via the ``chevron`` package.
Keep this in step with ``dva_processing.templates``: a template must render
identically whichever service asked for it.
"""

from __future__ import annotations

import json
from typing import Any

import chevron


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=lambda v: v.value)


class _AsJSON:
    """
    Prints as JSON when chevron inserts it.

    chevron inserts a falsy value (null, false, {}, []) as an empty string
    unless it carries ``_CHEVRON_return_scope_when_falsy``, so every wrapper
    sets it to have the value itself inserted.
    """

    _CHEVRON_return_scope_when_falsy = True

    def __str__(self) -> str:
        return _to_json(self)


class _JSONDict(_AsJSON, dict):
    """A dict chevron can still open as a section."""


class _JSONList(_AsJSON, list):
    """A list chevron can still iterate as a section."""


class _JSONScalar(_AsJSON):
    """``True``/``False``/``None``, keeping their truthiness for sections."""

    def __init__(self, value: bool | None) -> None:
        self.value = value

    def __bool__(self) -> bool:
        return bool(self.value)

    def __str__(self) -> str:
        return _to_json(self.value)


def _as_json_values(value: Any) -> Any:
    """
    Make every non-string value print as JSON rather than as Python.

    chevron inserts a value with ``str()``, so an object would otherwise
    render as ``{'a': True}`` – which no evaluator can read – instead of
    ``{"a": true}``. Strings and numbers already print as they should.
    """
    if isinstance(value, dict):
        return _JSONDict({key: _as_json_values(item) for key, item in value.items()})
    if isinstance(value, list):
        return _JSONList(_as_json_values(item) for item in value)
    if value is None or isinstance(value, bool):
        return _JSONScalar(value)
    return value


def render_template(implementation_template: str, model: dict[str, Any]) -> str:
    """
    Render a Handlebars ``{{var}}`` template string with a model dict.

    Objects, arrays, booleans and null are inserted as JSON. ``{{var}}``
    HTML-escapes what it inserts and ``{{{var}}}`` does not.
    """
    return chevron.render(implementation_template, _as_json_values(model))
