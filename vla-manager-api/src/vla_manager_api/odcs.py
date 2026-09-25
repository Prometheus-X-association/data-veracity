"""
The VLA as an Open Data Contract Standard (ODCS) document.

A VLA's requirements are the ``quality`` entries of its schema objects, as
ODCS places them and as DVA Processing's ``/evaluate-batch`` reads them
during attestation. Every VLA is checked against the same ODCS model
processing parses it with before it is stored, so a VLA the VLA Manager
accepts is one attestation can run.

VLAs stored before this held a looser shape – a string ``description``, a
single ``schema`` object and the requirements in a top-level ``quality``
array. :func:`upgrade_legacy` rewrites those as they are read.
"""

from __future__ import annotations

from typing import Any

from open_data_contract_standard.model import OpenDataContractStandard
from pydantic import ValidationError

from .models import QualityEngine

# The schema object requirements are attached to when a VLA declares none:
# the data the exchange carries, which is what the requirements check.
DEFAULT_SCHEMA_OBJECT: dict[str, Any] = {"name": "data", "logicalType": "object"}

_ENGINES = {engine.value for engine in QualityEngine}


class InvalidVLA(ValueError):
    """The document is not a VLA the DVA can evaluate; the message says why."""


def requirement(engine: QualityEngine, implementation: str) -> dict[str, Any]:
    """An ODCS ``DataQuality`` entry for an engine-run requirement."""
    return {"type": "custom", "engine": engine.value, "implementation": implementation}


def requirements(vla: dict[str, Any]) -> list[dict[str, Any]]:
    """Every requirement in the VLA, in the order processing evaluates them."""
    return [
        entry
        for schema_object in vla.get("schema") or []
        for entry in schema_object.get("quality") or []
    ]


def add_requirements(vla: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    """Append ``entries`` to the VLA's first schema object, adding one if needed."""
    if not entries:
        return
    schema = vla.get("schema") or [dict(DEFAULT_SCHEMA_OBJECT)]
    schema[0]["quality"] = list(schema[0].get("quality") or []) + entries
    vla["schema"] = schema


def _where(loc: tuple[int | str, ...]) -> str:
    return ".".join(str(part) for part in loc) or "the VLA"


def check(vla: dict[str, Any]) -> None:
    """
    Raise :class:`InvalidVLA` unless ``vla`` is an ODCS document whose
    requirements processing can run.

    Beyond ODCS itself: a requirement must name an engine the DVA implements
    and give its implementation, and must sit on a schema object – processing
    does not look for requirements on individual properties, so one there
    would never be checked.
    """
    try:
        OpenDataContractStandard.model_validate(vla)
    except ValidationError as exc:
        problems = "; ".join(
            f"{_where(error['loc'])}: {error['msg']}" for error in exc.errors()
        )
        raise InvalidVLA(f"The VLA is not a valid ODCS data contract: {problems}")

    for i, schema_object in enumerate(vla.get("schema") or []):
        for j, prop in enumerate(schema_object.get("properties") or []):
            if prop.get("quality"):
                raise InvalidVLA(
                    f"schema.{i}.properties.{j}.quality: requirements belong on "
                    "the schema object, not on one of its properties"
                )
        for j, entry in enumerate(schema_object.get("quality") or []):
            where = f"schema.{i}.quality.{j}"
            if entry.get("engine") not in _ENGINES:
                raise InvalidVLA(
                    f"{where}.engine: must be one of {', '.join(sorted(_ENGINES))}"
                )
            if not isinstance(entry.get("implementation"), str):
                raise InvalidVLA(f"{where}.implementation: must be a string")


def _legacy_properties(json_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """JSON-schema-style ``{"properties": {name: {"type": …}}}`` as ODCS properties."""
    return [
        {"name": name, **({"logicalType": d["type"]} if "type" in d else {})}
        for name, d in (json_schema.get("properties") or {}).items()
        if isinstance(d, dict)
    ]


def upgrade_legacy(vla: dict[str, Any]) -> dict[str, Any]:
    """
    Rewrite a VLA stored in the pre-ODCS shape as ODCS; others pass as they are.

    A string ``description`` becomes the contract's ``purpose``; a single
    ``schema`` object becomes the first of the list, its JSON-schema-style
    ``properties`` becoming ODCS ones; a top-level ``quality`` moves onto it.
    """
    if isinstance(vla.get("description"), str):
        vla["description"] = {"purpose": vla["description"]}

    schema = vla.get("schema")
    if isinstance(schema, dict):
        if isinstance(schema.get("properties"), dict):
            schema_object = dict(DEFAULT_SCHEMA_OBJECT)
            schema_object["properties"] = _legacy_properties(schema)
        else:
            schema_object = {**DEFAULT_SCHEMA_OBJECT, **schema}
        vla["schema"] = [schema_object]

    if "quality" in vla:
        legacy = vla.pop("quality") or []
        add_requirements(vla, [{"type": "custom", **entry} for entry in legacy])
    return vla
