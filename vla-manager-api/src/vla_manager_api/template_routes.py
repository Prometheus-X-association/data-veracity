"""FastAPI routes for VLA Template CRUD."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate as validate_json

from .dependencies import (
    get_requirement_evaluator,
    get_requirement_validator,
    get_template_repo,
)
from .errors import http_error
from .log import get_logger
from .models import (
    IDDTO,
    EvaluationFromTemplate,
    RenderResult,
    Template,
    TemplateNew,
    TemplatePatch,
    TemplateValidationResult,
)
from .template_repo import TemplateRepo
from .templates import render_template
from .validation import (
    ProcessingError,
    RequirementEvaluator,
    RequirementValidator,
    check_requirement,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/template", response_model=list[Template])
async def list_templates(
    repo: TemplateRepo = Depends(get_template_repo),
) -> list[Template]:
    return await repo.all()


@router.post("/template", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_template(
    template_req: TemplateNew, repo: TemplateRepo = Depends(get_template_repo)
) -> IDDTO:
    new_id = await repo.add(template_req)
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
) -> Template:
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
) -> Template:
    if id != patch.id:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "ID path parameter does not match ID in body",
        )
    updated = await repo.update(id, patch)
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
    em = template.evaluation_method
    try:
        rendered = render_template(em.implementation_template, model)
    except Exception as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST, "Failed to render template"
        ) from exc
    return RenderResult(engine=em.engine, implementation=rendered)


@router.post(
    "/template/{id}/validate",
    response_model=TemplateValidationResult,
    # The spec has `reason` absent on a pass and `implementation` absent
    # when rendering is what failed, so the unset fields are omitted rather
    # than sent as null.
    response_model_exclude_none=True,
)
async def validate_template_route(
    id: UUID,
    model: dict[str, Any],
    repo: TemplateRepo = Depends(get_template_repo),
    validator: RequirementValidator = Depends(get_requirement_validator),
) -> TemplateValidationResult:
    # Always a 200 once the template is found: every way this can go wrong
    # is something the author asked to be told about, so each is a verdict
    # in the body rather than an error status.
    template = await repo.by_id(id)
    if template is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )

    return await check_requirement(template.evaluation_method, model, validator)


@router.post("/evaluate/from-template")
async def evaluate_from_template(
    request: EvaluationFromTemplate,
    repo: TemplateRepo = Depends(get_template_repo),
    evaluator: RequirementEvaluator = Depends(get_requirement_evaluator),
) -> JSONResponse:
    """
    Run a template, rendered with a model, over sample data.

    The template is rendered here, where it lives, and the finished
    requirement is sent to DVA Processing's ``/evaluate``; its status and
    ``EvaluationResult`` are passed back as they are.
    """
    template = await repo.by_id(request.template_id)
    if template is None:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        )

    em = template.evaluation_method
    try:
        validate_json(instance=request.template_model, schema=em.variable_schema)
    except JSONSchemaValidationError as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            f"The template input does not match its variable schema: {exc.message}",
            type="INVALID_TEMPLATE_INPUT",
        ) from exc
    try:
        implementation = render_template(
            em.implementation_template, request.template_model
        )
    # chevron raises no one error type, so this matches the render route above.
    except Exception as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST, f"Failed to render template: {exc}"
        ) from exc

    try:
        code, body = await evaluator.evaluate(em.engine, implementation, request.data)
    except ProcessingError as exc:
        logger.warning("Could not evaluate rendered logic", error=str(exc))
        raise http_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"The evaluation service is unavailable: {exc}",
            type="EVALUATION_UNAVAILABLE",
        ) from exc
    return JSONResponse(status_code=code, content=body)
