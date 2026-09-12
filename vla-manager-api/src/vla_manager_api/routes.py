"""
FastAPI routes for the VLA Manager API.

VLA CRUD routes plus POST /vla/from-templates which fetches VLA
templates, renders each with a model, and merges the rendered quality
requirements into the VLA before persistence.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import get_repo, get_template_repo
from .errors import http_error
from .models import IDDTO, VLANew, VLANewFromTemplates
from .template_repo import TemplateRepo
from .templates import render_template
from .vla_repo import VLARepo

router = APIRouter()


def _wrap_vla(vla_req: VLANew) -> dict[str, Any]:
    """Wrap a partial ODCS payload with the boilerplate headers."""
    base: dict[str, Any] = {
        "apiVersion": "v3.0.2",
        "kind": "DataContract",
        "version": "0.1.0",
        "status": "active",
    }
    data = vla_req.model_dump(exclude_none=True, by_alias=True, mode="json")
    base.update(data)
    return base


@router.get("/vla")
async def list_vlas(repo: VLARepo = Depends(get_repo)) -> list[dict[str, Any]]:
    return await repo.all()


@router.get("/vla/{id}")
async def get_vla(id: UUID, repo: VLARepo = Depends(get_repo)) -> dict[str, Any]:
    vla = await repo.by_id(id)
    if vla is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "No VLA with the given ID exists")
    return vla


@router.post("/vla", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_vla(vla_req: VLANew, repo: VLARepo = Depends(get_repo)) -> IDDTO:
    vla = _wrap_vla(vla_req)
    new_id = await repo.add(vla)
    if new_id is None:
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to create VLA",
            type="UNKNOWN",
        )
    return IDDTO(id=new_id)


@router.post(
    "/vla/from-templates", status_code=status.HTTP_201_CREATED, response_model=IDDTO
)
async def create_vla_from_templates(
    vla_req: VLANewFromTemplates,
    repo: VLARepo = Depends(get_repo),
    template_repo: TemplateRepo = Depends(get_template_repo),
) -> IDDTO:
    base_vla = _wrap_vla(vla_req)
    base_vla.pop("qualityTemplates", None)

    rendered_quality: list[dict[str, Any]] = []
    for qt in vla_req.quality_templates:
        template = await template_repo.by_id(qt.id)
        if template is None:
            raise http_error(
                status.HTTP_404_NOT_FOUND, f"No template with ID {qt.id} exists"
            )
        em = template["evaluationMethod"]
        try:
            implementation = render_template(em["implementationTemplate"], qt.model)
        except Exception as exc:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                f"Failed to render template {qt.id}",
            ) from exc
        rendered_quality.append(
            {"engine": em["engine"], "implementation": implementation}
        )

    existing_quality = base_vla.get("quality") or []
    base_vla["quality"] = list(existing_quality) + rendered_quality

    new_id = await repo.add(base_vla)
    if new_id is None:
        raise http_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to create VLA",
            type="UNKNOWN",
        )
    return IDDTO(id=new_id)


@router.delete("/vla", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_vlas(repo: VLARepo = Depends(get_repo)) -> None:
    await repo.remove_all()
    return None
