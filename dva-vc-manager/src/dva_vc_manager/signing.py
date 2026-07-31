"""
JWS issuance and verification.

Facilitates the production of a compact JWS (``header.payload.signature``)
over a W3C VC 2.0 JSON-LD payload.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

# JWS header constants
JWS_HEADER_ALG = "EdDSA"
JWS_HEADER_TYPE = "VC+LD-JSON+JWS"
VC_CONTEXT = "https://www.w3.org/2018/credentials/v1"
VC_TYPE = "VerifiableCredential"
AOV_TYPE = "AttestationOfVeracity"


def _b64url(data: bytes) -> str:
    """Standard JWS base64url **without** padding (per RFC 7515 §2.2.2)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    """Inverse of :func:`_b64url` – re-adds padding before decoding."""
    pad = (-len(segment)) % 4
    return base64.urlsafe_b64decode(segment + "=" * pad)


def _json_compact(obj: dict[str, Any]) -> bytes:
    """Compact JSON encoding."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_aov_payload(claims: "AovClaims", issuer_did_key: str) -> dict[str, Any]:
    """Build the W3C VC 2.0 JSON-LD payload."""
    return {
        "@context": [VC_CONTEXT],
        "type": [VC_TYPE, AOV_TYPE],
        "issuer": issuer_did_key,
        "validFrom": claims.valid_since,
        "credentialSubject": {
            "vc_id": claims.vc_id,
            "valid_since": claims.valid_since,
            "subject": claims.subject,
            "issuer_id": claims.issuer_id,
            "record_id": claims.record_id,
            "contract_id": claims.contract_id,
            "data_exchange_id": claims.data_exchange_id,
            "payload": claims.payload,
        },
    }


def _jws_header() -> dict[str, str]:
    return {"alg": JWS_HEADER_ALG, "typ": JWS_HEADER_TYPE}


def sign_jws(claims: "AovClaims", signing_key: SigningKey, issuer_did_key: str) -> str:
    """Sign and produce a compact JWS string."""
    header_b64 = _b64url(_json_compact(_jws_header()))
    payload_b64 = _b64url(_json_compact(build_aov_payload(claims, issuer_did_key)))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    # PyNaCl SigningKey.sign returns a SignedMessage; .signature is the
    # detached raw 64-byte EdDSA signature.
    signature = signing_key.sign(signing_input).signature
    signature_b64 = _b64url(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_jws(jws: str, public_key: VerifyKey) -> bool:
    """Verify a compact JWS."""
    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("Compact JWS must have 3 dot-separated parts")
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    signature = _b64url_decode(parts[2])
    try:
        public_key.verify(signing_input, signature)
        return True
    except BadSignatureError:
        return False


def decode_payload(jws: str) -> dict[str, Any]:
    """Decode (without verifying) the payload middle segment of a JWS."""
    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("Compact JWS must have 3 dot-separated parts")
    return json.loads(_b64url_decode(parts[1]))


# AoV claims model – defined at the bottom of the module so older
# pydantic-style annotations above ("AovClaims") resolve via forward
# reference. Importing this class is the canonical way callers construct
# the claims payload.
from pydantic import BaseModel  # noqa: E402


class AovClaims(BaseModel):
    """The eight AoV credentialSubject claims."""

    vc_id: str
    valid_since: str
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    data_exchange_id: str
    payload: str

    model_config = {"populate_by_name": True}
