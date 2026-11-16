"""
Orchestrates the edge node demo.

The Dataspace Connector (PDC) POSTs the data to analyse to `/analyse`: the data
itself (a list of xAPI statements), or, in a service chain, an envelope
`{"data": ..., "contract": ..., "params": {...}}`.  The data goes through

 1. the anonymization service,
 2. the DVA (Data Veracity Assurance), which attests the anonymized data against a VLA,
 3. the aggregation service, which gets the attested, anonymized data,
 4. the DVA again, which attests the aggregated data against a second VLA,

and the aggregated data is sent back, together with the two attestations (AoVs).  If
either attestation fails, the flow stops there and nothing is returned but the reason.

Configuration (environment variables):

  ANONYMIZED_VLA_ID  VLA the anonymized data is attested against, unless the request names
                     one in `params.anonymizedVlaID` (which wins)
  AGGREGATED_VLA_ID  VLA the aggregated data is attested against, unless the request names
                     one in `params.aggregatedVlaID` (which wins)
  DVA_URL            base URL of the DVA API (default: http://dva-api-provider:9090)
  ANONYMIZER_URL     anonymization endpoint (default: http://xapi-anonymizer:8001/api/anonymize)
  AGGREGATOR_URL     aggregation endpoint (default: http://xapi-aggregation:8002/api/aggregate)
  TIMEOUT_SECONDS    timeout of each call to another service (default: 30)
"""

import logging
import os
import uuid
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

# The steps of the flow, as reported in errors
ANONYMIZATION = "anonymization"
ATTESTATION_ANONYMIZED = "attestation-anonymized"
AGGREGATION = "aggregation"
ATTESTATION_AGGREGATED = "attestation-aggregated"


@dataclass(frozen=True)
class Settings:
    anonymized_vla_id: Optional[str] = None
    aggregated_vla_id: Optional[str] = None
    dva_url: str = "http://dva-api-provider:9090"
    anonymizer_url: str = "http://xapi-anonymizer:8001/api/anonymize"
    aggregator_url: str = "http://xapi-aggregation:8002/api/aggregate"
    timeout_seconds: float = 30.0

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            anonymized_vla_id=os.environ.get("ANONYMIZED_VLA_ID", "").strip() or None,
            aggregated_vla_id=os.environ.get("AGGREGATED_VLA_ID", "").strip() or None,
            dva_url=os.environ.get("DVA_URL", Settings.dva_url).rstrip("/"),
            anonymizer_url=os.environ.get("ANONYMIZER_URL", Settings.anonymizer_url),
            aggregator_url=os.environ.get("AGGREGATOR_URL", Settings.aggregator_url),
            timeout_seconds=float(os.environ.get("TIMEOUT_SECONDS", Settings.timeout_seconds)),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


async def get_client(settings: Settings = Depends(get_settings)) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
        yield client


app = FastAPI(title="Edge node server demo")


class UpstreamError(Exception):
    """A service this one depends on did not do its part."""

    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.message = message


class AttestationRefused(Exception):
    """The DVA found that the data does not satisfy the VLA."""

    def __init__(self, stage: str, evaluation_results: list[Any]):
        super().__init__(stage)
        self.stage = stage
        self.evaluation_results = evaluation_results


@app.exception_handler(UpstreamError)
async def upstream_error_handler(_: Request, error: UpstreamError) -> JSONResponse:
    logger.error("%s failed: %s", error.stage, error.message)
    return JSONResponse(status_code=502, content={"stage": error.stage, "detail": error.message})


@app.exception_handler(AttestationRefused)
async def attestation_refused_handler(_: Request, refusal: AttestationRefused) -> JSONResponse:
    logger.info("%s: the data does not satisfy the VLA, the flow stops here", refusal.stage)
    return JSONResponse(
        status_code=422,
        content={
            "stage": refusal.stage,
            "detail": "the data does not satisfy the VLA",
            "evaluationResults": refusal.evaluation_results,
        },
    )


def as_uuid(value: Optional[str]) -> str:
    """A UUID for a PDC identifier: itself if it is one, otherwise derived from it (stably)."""
    if not value:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return str(uuid.uuid5(_ID_NAMESPACE, value))


async def _post(client: httpx.AsyncClient, stage: str, url: str, body: Any) -> Any:
    """The JSON the service at `url` answers with."""
    try:
        response = await client.post(url, json=body)
    except httpx.HTTPError as e:
        raise UpstreamError(stage, f"{url} could not be reached: {e!r}") from e
    if response.is_error:
        raise UpstreamError(stage, f"{url} answered {response.status_code}: {response.text[:500]}")
    try:
        return response.json()
    except ValueError as e:
        raise UpstreamError(stage, f"{url} did not answer with JSON") from e


async def anonymize(client: httpx.AsyncClient, settings: Settings, data: Any) -> list[Any]:
    """The anonymized statements: the data is POSTed as the JSON body, and the anonymized
    statements are the JSON list the anonymization service answers with."""
    anonymized = await _post(client, ANONYMIZATION, settings.anonymizer_url, data)
    if not isinstance(anonymized, list):
        raise UpstreamError(ANONYMIZATION, f"{settings.anonymizer_url} did not answer with a list")
    return anonymized


async def aggregate(client: httpx.AsyncClient, settings: Settings, statements: list[Any]) -> list[Any]:
    """The aggregated data (one row per student): the statements are POSTed as the JSON
    body, and the rows are the JSON list the aggregation service answers with."""
    rows = await _post(client, AGGREGATION, settings.aggregator_url, statements)
    if not isinstance(rows, list):
        raise UpstreamError(AGGREGATION, f"{settings.aggregator_url} did not answer with a list")
    return rows


def unwrap(body: Any) -> tuple[Any, dict[str, Any], Optional[str]]:
    """The data, the params and the contract of a request body.

    In a service chain the PDC wraps the data: an object with `data` and `params` and/or
    `contract`.  Any other body is the data itself, without params.
    """
    if isinstance(body, dict) and "data" in body and ("params" in body or "contract" in body):
        params = body.get("params")
        return body["data"], params if isinstance(params, dict) else {}, body.get("contract")
    return body, {}, None


def _vla_id(what: str, param: str, setting: str, from_params: Any, configured: Optional[str]) -> str:
    vla_id = from_params or configured
    if not vla_id:
        raise HTTPException(
            status_code=422, detail=f"no VLA for the {what} data: set {setting} or send params.{param}"
        )
    try:
        return str(uuid.UUID(str(vla_id)))
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"the VLA ID {vla_id!r} for the {what} data is not a valid UUID"
        ) from None


def vla_ids_for(settings: Settings, params: dict[str, Any]) -> tuple[str, str]:
    """The VLAs for the anonymized and for the aggregated data: the ones named in the
    request's params, else the configured ones."""
    return (
        _vla_id("anonymized", "anonymizedVlaID", "ANONYMIZED_VLA_ID",
                params.get("anonymizedVlaID"), settings.anonymized_vla_id),
        _vla_id("aggregated", "aggregatedVlaID", "AGGREGATED_VLA_ID",
                params.get("aggregatedVlaID"), settings.aggregated_vla_id),
    )


async def attest(
    client: httpx.AsyncClient,
    settings: Settings,
    stage: str,
    exchange_id: str,
    contract_id: str,
    vla_id: str,
    data: Any,
) -> dict[str, Any]:
    """The DVA's attestation of the data against the VLA: the AoV and the evaluation results.

    @raises AttestationRefused if the data does not satisfy the VLA
    """
    attestation = await _post(
        client,
        stage,
        f"{settings.dva_url}/attestation",
        {"exchangeID": exchange_id, "contractID": contract_id, "vlaID": vla_id, "data": data},
    )
    if not (attestation.get("evaluationPassing") and attestation.get("jws")):
        raise AttestationRefused(stage, attestation.get("evaluationResults", []))
    return {
        "vlaID": vla_id,
        "jws": attestation["jws"],
        "evaluationResults": attestation.get("evaluationResults", []),
    }


@app.post("/analyse")
async def analyse(
    request: Request,
    body: Any = Body(...),
    settings: Settings = Depends(get_settings),
    client: httpx.AsyncClient = Depends(get_client),
) -> JSONResponse:
    """Anonymize the data, attest it, aggregate it, attest the aggregate, and return it."""
    data, params, contract = unwrap(body)
    anonymized_vla, aggregated_vla = vla_ids_for(settings, params)

    # The PDC identifies the exchange and the contract in its headers (the contract
    # also in the body, in a service chain)
    exchange_id = as_uuid(request.headers.get("x-ptx-dataExchangeId"))
    contract_id = as_uuid(request.headers.get("x-ptx-contractId") or contract)

    anonymized = await anonymize(client, settings, data)
    anonymized_attestation = await attest(
        client, settings, ATTESTATION_ANONYMIZED, exchange_id, contract_id, anonymized_vla, anonymized
    )

    aggregated = await aggregate(client, settings, anonymized)
    aggregated_attestation = await attest(
        client, settings, ATTESTATION_AGGREGATED, exchange_id, contract_id, aggregated_vla, aggregated
    )

    return JSONResponse(
        content={
            "data": aggregated,
            "attestations": {"anonymized": anonymized_attestation, "aggregated": aggregated_attestation},
            "exchangeID": exchange_id,
            "contractID": contract_id,
        }
    )
