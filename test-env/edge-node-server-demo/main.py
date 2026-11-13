"""
Orchestrates the edge node demo.

The Dataspace Connector (PDC) POSTs the data to analyse to `/analyse`.  The
data is

 1. anonymized by the anonymization service,
 2. attested by the DVA (Data Veracity Assurance) against a fixed VLA, and
 3. if the attestation succeeds, forwarded to the next endpoint.

Configuration (environment variables):

  VLA_ID          ID of the VLA to attest against (required; the same for every request)
  DVA_URL         base URL of the DVA API (default: http://dva-api-provider:9090)
  ANONYMIZER_URL  endpoint of the anonymization service; not set: a mock is used, which
                  leaves the data as it is (the real service is provided separately)
  FORWARD_URL     endpoint the attested data is forwarded to; not set: not forwarded
  TIMEOUT_SECONDS timeout of each call to another service (default: 30)
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, AsyncIterator, Optional

import httpx
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("edge-node-server-demo")

# Opaque PDC identifiers (Mongo ObjectIds, contract URLs) are mapped into this
# namespace, because the DVA wants UUIDs for the exchange and the contract.
_ID_NAMESPACE = uuid.UUID("6f1c2d8e-4a57-4c0b-9a3e-2d7b5f0e8c11")


@dataclass(frozen=True)
class Settings:
    vla_id: str
    dva_url: str = "http://dva-api-provider:9090"
    anonymizer_url: Optional[str] = None
    forward_url: Optional[str] = None
    timeout_seconds: float = 30.0

    @staticmethod
    def from_env() -> "Settings":
        vla_id = os.environ.get("VLA_ID", "").strip()
        if not vla_id:
            raise RuntimeError("VLA_ID is not set: the VLA to attest against is required")
        return Settings(
            vla_id=vla_id,
            dva_url=os.environ.get("DVA_URL", Settings.dva_url).rstrip("/"),
            anonymizer_url=os.environ.get("ANONYMIZER_URL") or None,
            forward_url=os.environ.get("FORWARD_URL") or None,
            timeout_seconds=float(os.environ.get("TIMEOUT_SECONDS", Settings.timeout_seconds)),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


async def get_client(settings: Settings = Depends(get_settings)) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
        yield client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Fail at startup, not on the first request, if the configuration is incomplete
    app.dependency_overrides.get(get_settings, get_settings)()
    yield


app = FastAPI(title="Edge node server demo", lifespan=lifespan)


class UpstreamError(Exception):
    """A service this one depends on did not do its part."""

    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.message = message


@app.exception_handler(UpstreamError)
async def upstream_error_handler(_: Request, error: UpstreamError) -> JSONResponse:
    logger.error("%s failed: %s", error.stage, error.message)
    return JSONResponse(status_code=502, content={"stage": error.stage, "detail": error.message})


def as_uuid(value: Optional[str]) -> str:
    """A UUID for a PDC identifier: itself if it is one, otherwise derived from it (stably)."""
    if not value:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return str(uuid.uuid5(_ID_NAMESPACE, value))


async def _post(client: httpx.AsyncClient, stage: str, url: str, body: Any) -> httpx.Response:
    try:
        response = await client.post(url, json=body)
    except httpx.HTTPError as e:
        raise UpstreamError(stage, f"{url} could not be reached: {e!r}") from e
    if response.is_error:
        raise UpstreamError(stage, f"{url} answered {response.status_code}: {response.text[:500]}")
    return response


def mock_anonymize(data: Any) -> Any:
    """Stands in for the anonymization service until it is available: changes nothing."""
    return data


async def anonymize(client: httpx.AsyncClient, settings: Settings, data: Any) -> tuple[Any, str]:
    """The anonymized data, and how it was anonymized: "applied" by the anonymization
    service, or "mock" by the stand-in that leaves the data as it is.

    Assumed contract of the anonymization service (to be confirmed): the data is
    POSTed as the JSON body, and the anonymized data is the JSON body of the answer.
    """
    if settings.anonymizer_url is None:
        logger.warning("ANONYMIZER_URL is not set: using the MOCK anonymizer, the data is not anonymized")
        return mock_anonymize(data), "mock"
    response = await _post(client, "anonymization", settings.anonymizer_url, data)
    try:
        return response.json(), "applied"
    except ValueError as e:
        raise UpstreamError("anonymization", "the anonymization service did not answer with JSON") from e


async def attest(
    client: httpx.AsyncClient, settings: Settings, exchange_id: str, contract_id: str, data: Any
) -> dict[str, Any]:
    response = await _post(
        client,
        "attestation",
        f"{settings.dva_url}/attestation",
        {"exchangeID": exchange_id, "contractID": contract_id, "vlaID": settings.vla_id, "data": data},
    )
    try:
        return response.json()
    except ValueError as e:
        raise UpstreamError("attestation", "the DVA did not answer with JSON") from e


@app.post("/analyse")
async def analyse(
    request: Request,
    data: Any = Body(...),
    settings: Settings = Depends(get_settings),
    client: httpx.AsyncClient = Depends(get_client),
) -> JSONResponse:
    """Anonymize the data, attest it, and forward it if the attestation succeeds."""
    # The PDC sends the identifiers of the exchange and the contract along with the data
    exchange_id = as_uuid(request.headers.get("x-ptx-dataExchangeId"))
    contract_id = as_uuid(request.headers.get("x-ptx-contractId"))

    anonymized, anonymization = await anonymize(client, settings, data)

    attestation = await attest(client, settings, exchange_id, contract_id, anonymized)
    passing = bool(attestation.get("evaluationPassing")) and bool(attestation.get("jws"))
    if not passing:
        logger.info("exchange %s: the data does not satisfy the VLA, not forwarded", exchange_id)
        return JSONResponse(
            status_code=422,
            content={
                "detail": "the data does not satisfy the VLA, so it was not forwarded",
                "anonymization": anonymization,
                "evaluationResults": attestation.get("evaluationResults", []),
            },
        )

    forwarded = settings.forward_url is not None
    if forwarded:
        await _post(client, "forward", settings.forward_url, anonymized)
    else:
        logger.warning("FORWARD_URL is not set: the attested data is NOT forwarded")

    return JSONResponse(
        content={
            "anonymization": anonymization,
            "attestation": {
                "exchangeID": exchange_id,
                "contractID": contract_id,
                "vlaID": settings.vla_id,
                "jws": attestation["jws"],
                "evaluationResults": attestation.get("evaluationResults", []),
            },
            "forwarded": forwarded,
        }
    )
