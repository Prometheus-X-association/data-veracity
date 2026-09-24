"""
How template placeholders are filled in.

``vla-manager-api/tests/test_templates.py`` holds the same cases: both
services must render a template identically.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from dva_processing.templates import render_template


@pytest.mark.parametrize(
    ("template", "model", "rendered"),
    [
        (".x <= {{max}}", {"max": 10}, ".x <= 10"),
        (".x == {{flag}}", {"flag": True}, ".x == true"),
        (".x == {{flag}}", {"flag": False}, ".x == false"),
        (".x == {{v}}", {"v": None}, ".x == null"),
        (".x == {{v}}", {"v": 0}, ".x == 0"),
        ("{{{v}}}", {"v": {}}, "{}"),
        ("{{{v}}}", {"v": []}, "[]"),
        ("{{{v}}}", {"v": ["a", 1, True, None]}, '["a", 1, true, null]'),
        ("{{{v}}}", {"v": {"a": {"b": [False]}}}, '{"a": {"b": [false]}}'),
        ('.s == "{{s}}"', {"s": "plain"}, '.s == "plain"'),
        ("{{v.type}}", {"v": {"type": "object"}}, "object"),
        (".x == {{missing}}", {}, ".x == "),
    ],
)
def test_non_string_values_are_inserted_as_json(
    template: str, model: dict[str, Any], rendered: str
) -> None:
    assert render_template(template, model) == rendered


def test_an_object_renders_as_a_parseable_json_schema() -> None:
    schema = {"type": "object", "required": ["id"], "additionalProperties": False}

    assert json.loads(render_template("{{{schema}}}", {"schema": schema})) == schema


def test_double_braces_html_escape_and_triple_braces_do_not() -> None:
    model = {"v": {"k": 'a"b'}}

    assert render_template("{{v}}", model) == "{&quot;k&quot;: &quot;a\\&quot;b&quot;}"
    assert render_template("{{{v}}}", model) == '{"k": "a\\"b"}'


@pytest.mark.parametrize(
    ("template", "model", "rendered"),
    [
        ("{{#v}}[{{.}}]{{/v}}", {"v": ["a", "b"]}, "[a][b]"),
        ("{{#v}}{{type}}{{/v}}", {"v": {"type": "object"}}, "object"),
        ("{{#v}}shown{{/v}}", {"v": True}, "shown"),
        ("{{#v}}shown{{/v}}", {"v": False}, ""),
        ("{{#v}}shown{{/v}}", {"v": None}, ""),
        ("{{#v}}shown{{/v}}", {"v": []}, ""),
        ("{{^v}}none{{/v}}", {"v": False}, "none"),
    ],
)
def test_sections_still_see_the_original_values(
    template: str, model: dict[str, Any], rendered: str
) -> None:
    assert render_template(template, model) == rendered
