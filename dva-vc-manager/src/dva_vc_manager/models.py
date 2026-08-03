"""
HTTP request/response models for /aov/issue and /aov/verify.

The AoV endpoints speak ``camelCase`` on the wire while the Python
attribute names stay ``snake_case``.  ``populate_by_name`` keeps
``snake_case`` accepted on input too, which is what the tests send.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_CAMEL = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EvaluationResultDTO(BaseModel):
    """One row of the veracity-check results array."""

    engine: Optional[str] = None
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class AovIssueRequest(BaseModel):
    """
    Body of ``POST /aov/issue``.

    The DVA API posts the seven AoV claims fields plus the veracity-check
    results array.  The VC Manager generates a fresh UUID for the credential and
    signs the AoV payload as a compact JWS.
    """

    model_config = _CAMEL

    valid_since: str
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    data_exchange_id: str
    payload: str
    evaluation_results: list[EvaluationResultDTO]


class AovIssueResponse(BaseModel):
    """
    Returned by ``POST /aov/issue``.

    The JWS contains the issuer ``did:key``, the VC UUID, and the issuance
    timestamp, so they are not duplicated in the response body.
    """

    model_config = _CAMEL

    jws: str


class AovVerifyRequest(BaseModel):
    """
    Body of ``POST /aov/verify``.

    Only the compact JWS string is supplied; the issuer ``did:key`` is
    extracted from the JWS payload.
    """

    model_config = _CAMEL

    jws: str


class AovVerifyResponse(BaseModel):
    """Returned by ``POST /aov/verify``."""

    verified: bool
    reason: Optional[str] = None


class WhitelistAddRequest(BaseModel):
    """Body of ``POST /admin/whitelist``."""

    did_key: str
    label: Optional[str] = None


class WhitelistEntryDTO(BaseModel):
    """Returned by ``GET /admin/whitelist`` and ``POST /admin/whitelist``."""

    id: UUID
    did_key: str
    label: Optional[str] = None


class OwnKeyDTO(BaseModel):
    """Returned by ``GET /admin/keys``.

    Read-only view of this service's signing ``did:key``.
    """

    issuer_did_key: str
    key_path: str
