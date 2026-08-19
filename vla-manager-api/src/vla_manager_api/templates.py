"""
Template rendering for VLA Templates.

Ported from the deleted Kotlin ``Template.render`` (service/templates.kt).
Uses Handlebars-compatible ``{{var}}`` syntax via the ``chevron`` package,
byte-compatible with the old Kotlin Handlebars output.
"""

from __future__ import annotations

from typing import Any

import chevron


def render_template(implementation_template: str, model: dict[str, Any]) -> str:
    """Render a Handlebars ``{{var}}`` template string with a model dict."""
    return chevron.render(implementation_template, model)
