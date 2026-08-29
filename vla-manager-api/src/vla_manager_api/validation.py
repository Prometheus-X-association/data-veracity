from __future__ import annotations

from typing import Any, Protocol

import httpx2


class RequirementValidator(Protocol):
    async def validate(self, engine: str, implementation: str) -> dict[str, Any]: ...


class ProcessingRequirementValidator:
    def __init__(self, processing_url: str) -> None:
        self._processing_url = processing_url.rstrip("/")

    async def validate(self, engine: str, implementation: str) -> dict[str, Any]:
        async with httpx2.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self._processing_url}/validate-requirement",
                json={"engine": engine, "implementation": implementation},
            )
            response.raise_for_status()
            return response.json()
