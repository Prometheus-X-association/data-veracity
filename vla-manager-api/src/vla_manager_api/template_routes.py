"""FastAPI routes for VLA Template CRUD."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate as validate_json

from .dependencies import get_requirement_validator, get_template_repo
from .errors import http_error
from .models import (
    IDDTO,
    RenderResult,
    Template,
    TemplateNew,
    TemplatePatch,
    TemplateValidationRequest,
    TemplateValidationResult,
)
from .template_repo import TemplateRepo
from .templates import render_template
from .validation import RequirementValidator

router = APIRouter()


@router.get("/template", response_model=list[Template])
async def list_templates(
    repo: TemplateRepo = Depends(get_template_repo),
) -> list[dict[str, Any]]:
    return await repo.all()


@router.post("/template", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_template(
    template_req: TemplateNew, repo: TemplateRepo = Depends(get_template_repo)
) -> IDDTO:
    template = template_req.model_dump(by_alias=True, exclude_none=True)
    new_id = await repo.add(template)
    if new_id is None:
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to create template",
            type="UNKNOWN",
        )
    return IDDTO(id=new_id)


@router.get("/template/{id}", response_model=Template)
async def get_template(
    id: UUID, repo: TemplateRepo = Depends(get_template_repo)
) -> dict[str, Any]:
    template = await repo.by_id(id)
    if template is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )
    return template


@router.patch("/template/{id}", response_model=Template)
async def update_template(
    id: UUID,
    patch: TemplatePatch,
    repo: TemplateRepo = Depends(get_template_repo),
) -> dict[str, Any]:
    if id != patch.id:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "ID path parameter does not match ID in body",
        )
    patch_dict = patch.model_dump(by_alias=True, exclude_none=True)
    updated = await repo.update(id, patch_dict)
    if updated is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )
    return updated


@router.delete("/template/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    id: UUID, repo: TemplateRepo = Depends(get_template_repo)
) -> None:
    if not await repo.remove(id):
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )
    return None


@router.delete("/template", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_templates(
    repo: TemplateRepo = Depends(get_template_repo),
) -> None:
    await repo.remove_all()
    return None


@router.post("/template/{id}/render", response_model=RenderResult)
async def render_template_route(
    id: UUID,
    model: dict[str, Any],
    repo: TemplateRepo = Depends(get_template_repo),
) -> RenderResult:
    template = await repo.by_id(id)
    if template is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )
    em = template["evaluationMethod"]
    try:
        rendered = render_template(em["implementationTemplate"], model)
    except Exception as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST, "Failed to render template"
        ) from exc
    return RenderResult(engine=em["engine"], implementation=rendered)


@router.post("/template/{id}/validate", response_model=TemplateValidationResult)
async def validate_template_route(
    id: UUID,
    request: TemplateValidationRequest,
    repo: TemplateRepo = Depends(get_template_repo),
    validator: RequirementValidator = Depends(get_requirement_validator),
) -> TemplateValidationResult:
    template = await repo.by_id(id)
    if template is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )

    em = template["evaluationMethod"]
    try:
        validate_json(instance=request.model, schema=em["variableSchema"])
    except JSONSchemaValidationError as exc:
        return TemplateValidationResult(
            valid=False,
            status="INVALID",
            code="TEMPLATE_INPUT_INVALID",
            engine=em["engine"],
            message="The template input does not match its variable schema.",
            details=exc.message,
        )

    try:
        rendered = render_template(em["implementationTemplate"], request.model)
    except Exception as exc:
        return TemplateValidationResult(
            valid=False,
            status="INVALID",
            code="TEMPLATE_RENDER_FAILED",
            engine=em["engine"],
            message="The template could not be rendered.",
            details=str(exc),
        )

    try:
        result = await validator.validate(em["engine"], rendered)
    except Exception as exc:
        return TemplateValidationResult(
            valid=False,
            status="UNAVAILABLE",
            code="EVALUATION_ENGINE_UNAVAILABLE",
            engine=em["engine"],
            message="The evaluation service is unavailable.",
            details=str(exc),
            implementation=rendered,
        )
    return TemplateValidationResult(**result, implementation=rendered)
