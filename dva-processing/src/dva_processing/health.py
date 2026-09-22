"""
Health endpoints; see ``docs/health-checks.md``.

Evaluation is stateless and needs no other service, so both ``GET /livez``
and ``GET /readyz`` answer ``{"status": "pass"}`` as long as the process
serves HTTP.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/livez")
@router.get("/readyz")
async def health() -> JSONResponse:
    return JSONResponse({"status": "pass"}, media_type="application/health+json")
