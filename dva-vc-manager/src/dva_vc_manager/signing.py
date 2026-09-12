"""
JWS issuance and verification.

Produces a compact JWS (``header.payload.signature``) over a W3C VC 2.0
JSON-LD payload.  The JOSE layer is handled by ``joserfc``; this module
owns the AoV payload shape.
"""

from __future__ import annotations

import json
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from joserfc import jws
from joserfc.errors import BadSignatureError, JoseError
from joserfc.jwk import OKPKey
from pydantic import BaseModel

# JWS header constants.  RFC 9864 deprecates the polymorphic "EdDSA"
# identifier in favour of the fully specified "Ed25519".
JWS_HEADER_ALG = "Ed25519"
JWS_HEADER_TYPE = "VC+LD-JSON+JWS"
VC_CONTEXT = "https://www.w3.org/ns/credentials/v2"
VC_TYPE = "VerifiableCredential"
AOV_TYPE = "AttestationOfVeracity"

# joserfc's default registry admits only its "recommended" algorithms, which
# includes neither Ed25519 nor EdDSA, so the registry must be named explicitly.
# That doubles as an allowlist: a JWS declaring any other alg -- including the
# deprecated "EdDSA" -- is rejected before its signature is ever checked.
_REGISTRY = jws.JWSRegistry(algorithms=[JWS_HEADER_ALG])


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


class MalformedJws(ValueError):
    """The string is not a well-formed compact JWS."""


def split_jws(jws_str: str) -> tuple[str, str, str]:
    """Split a compact JWS into its header, payload and signature segments."""
    parts = jws_str.split(".")
    if len(parts) != 3:
        raise MalformedJws("Compact JWS must have 3 dot-separated parts")
    return parts[0], parts[1], parts[2]


def _json_compact(obj: dict[str, Any]) -> bytes:
    """Compact JSON encoding."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_aov_payload(claims: AovClaims, issuer_did_key: str) -> dict[str, Any]:
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


def sign_jws(
    claims: AovClaims, signing_key: Ed25519PrivateKey, issuer_did_key: str
) -> str:
    """Sign and produce a compact JWS string."""
    header = {"alg": JWS_HEADER_ALG, "typ": JWS_HEADER_TYPE}
    payload = _json_compact(build_aov_payload(claims, issuer_did_key))
    return jws.serialize_compact(
        header, payload, OKPKey.import_key(signing_key), registry=_REGISTRY
    )


def verify_jws(jws_str: str, public_key: Ed25519PublicKey) -> bool:
    """
    Verify a compact JWS.

    Returns False when the signature does not check out; raises
    :class:`MalformedJws` when the input is not a usable JWS at all.
    """
    try:
        jws.deserialize_compact(
            jws_str, OKPKey.import_key(public_key), registry=_REGISTRY
        )
    except BadSignatureError:
        return False
    except JoseError as e:
        # joserfc raises JoseError subclasses, which are not ValueErrors;
        # callers here treat malformed input as ValueError.
        raise MalformedJws(str(e)) from e
    return True


def decode_payload(jws_str: str) -> dict[str, Any]:
    """Decode (without verifying) the payload segment of a JWS."""
    try:
        extracted = jws.extract_compact(jws_str.encode("ascii"))
    except (JoseError, UnicodeEncodeError) as e:
        raise MalformedJws(str(e)) from e

    payload = json.loads(extracted.payload)
    if not isinstance(payload, dict):
        raise MalformedJws(
            f"JWS payload must be a JSON object, got {type(payload).__name__}"
        )
    return payload
