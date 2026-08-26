"""
Pydantic v2 schemas accepted/returned by the VLA Manager API.

The wire format is ``camelCase`` while the Python attribute names stay
``snake_case``; a shared ``alias_generator`` derives the aliases rather
than each field spelling its own out. ``populate_by_name`` keeps
``snake_case`` accepted on input too.

Field-level constraints track ``docs/spec/vla-manager-api.yaml``: the
enums come from its ``QualityEngine`` / ``CriterionType`` /
``QualityAspect`` schemas, and ``extra`` mirrors each schema's
``additionalProperties``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# ``extra`` mirrors the spec's ``additionalProperties`` per schema.
_CAMEL = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
_CAMEL_OPEN = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")


class QualityEngine(str, Enum):
    """Veracity-check engine (spec ``QualityEngine``)."""

    SCHEMA = "SCHEMA"
    GREAT_EXPECTATIONS = "GREAT_EXPECTATIONS"
    JQ = "JQ"


class CriterionType(str, Enum):
    """Shape of the criterion a template expresses (spec ``CriterionType``)."""

    VALID_INVALID = "VALID_INVALID"
    IN_RANGE = "IN_RANGE"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"


class QualityAspect(str, Enum):
    """Data-quality aspect a template targets (spec ``QualityAspect``)."""

    SYNTAX = "SYNTAX"
    TIMELINESS = "TIMELINESS"
    ACCURACY = "ACCURACY"
    COMPLETENESS = "COMPLETENESS"
    CONSISTENCY = "CONSISTENCY"


class DataQuality(BaseModel):
    """A single quality requirement (ODCS DataQuality fragment)."""

    model_config = _CAMEL

    engine: QualityEngine
    implementation: str


class VLANew(BaseModel):
    """
    Body of ``POST /vla``. All fields optional — partial ODCS payload.

    ``additionalProperties`` is true in the spec, so unrecognised ODCS
    fields are kept and persisted rather than dropped.

    The ``schema`` field carries an explicit alias because ``schema`` is a
    reserved attribute name on pydantic BaseModel. Inputs and outputs use
    the JSON key ``schema`` transparently.
    """

    model_config = _CAMEL_OPEN

    description: Optional[str] = None
    servers: Optional[list[Any]] = None
    schema_: Optional[dict[str, Any]] = Field(default=None, alias="schema")
    quality: Optional[list[DataQuality]] = None
    price: Optional[dict[str, Any]] = None
    team: Optional[list[Any]] = None
    roles: Optional[list[Any]] = None
    sla_properties: Optional[list[Any]] = None
    support: Optional[list[Any]] = None
    tags: Optional[list[Any]] = None


class IDDTO(BaseModel):
    """Identifier of a newly created resource (spec ``Id``)."""

    model_config = _CAMEL

    id: UUID


class TemplateInstantiation(BaseModel):
    """
    One entry in ``VLANewFromTemplates.qualityTemplates`` — a template id
    plus the model dict to render it with.
    """

    model_config = _CAMEL

    id: UUID
    model: dict[str, Any]


class VLANewFromTemplates(VLANew):
    """
    Body of ``POST /vla/from-templates``. Extends VLANew with a
    ``qualityTemplates`` array whose entries are rendered and merged into
    the VLA's ``quality`` array before persistence.
    """

    model_config = _CAMEL_OPEN

    quality_templates: list[TemplateInstantiation]


class ErrDTO(BaseModel):
    """Problem detail returned on error responses (spec ``Error``)."""

    model_config = _CAMEL

    type: str
    title: str


# ---------------------------------------------------------------------------
# Template models — ported from the deleted Kotlin ``Template.kt`` (commit
# ba876ff~1). Wire format is camelCase to remain byte-compatible with the
# existing VLA Manager Vue UI and the OpenAPI spec.
# ---------------------------------------------------------------------------


class EvaluationMethod(BaseModel):
    """Renderable evaluation method inside a Template."""

    model_config = _CAMEL

    engine: QualityEngine
    variable_schema: dict[str, Any]
    implementation_template: str


class TemplateNew(BaseModel):
    """Body of ``POST /template`` — create a new template (no id)."""

    model_config = _CAMEL

    name: str
    description: Optional[str] = None
    criterion_type: CriterionType
    target_aspect: QualityAspect
    evaluation_method: EvaluationMethod


class TemplatePatch(BaseModel):
    """
    Body of ``PATCH /template/{id}`` — partial update. ``id`` must match
    the path parameter.
    """

    model_config = _CAMEL

    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    criterion_type: Optional[CriterionType] = None
    target_aspect: Optional[QualityAspect] = None
    evaluation_method: Optional[EvaluationMethod] = None


class Template(BaseModel):
    """Full template representation returned by GET endpoints."""

    model_config = _CAMEL

    id: UUID
    name: str
    description: Optional[str] = None
    criterion_type: CriterionType
    target_aspect: QualityAspect
    evaluation_method: EvaluationMethod


class RenderResult(BaseModel):
    """
    Result of rendering a template — a single DataQuality fragment.

    Kept distinct from :class:`DataQuality` because the spec declares the
    two schemas separately, even though their shape is identical.
    """

    model_config = _CAMEL

    engine: QualityEngine
    implementation: str
