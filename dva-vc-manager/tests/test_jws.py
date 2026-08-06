"""JWS sign+verify tests."""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dva_vc_manager.signing import (
    AovClaims,
    MalformedJws,
    decode_payload,
    sign_jws,
    verify_jws,
)


def _sample_claims() -> AovClaims:
    return AovClaims(
        vc_id="urn:uuid:11111111-2222-3333-4444-555555555555",
        valid_since="2024-01-01T00:00:00Z",
        subject="did:web:data-consumer.example",
        issuer_id="did:web:data-provider.example",
        record_id="rec-0001",
        contract_id="contract-0001",
        data_exchange_id="xchg-0001",
        payload="checksum:sha256:abcdef0123456789",
    )


_KNOWN_DID_KEY = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def test_signs_and_verifies_a_valid_aov() -> None:
    signing_key = Ed25519PrivateKey.generate()
    public_key = signing_key.public_key()

    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)

    assert jws, "JWS must not be empty"
    assert jws.count(".") == 2, "Compact JWS must have 3 dot-separated parts"

    ok = verify_jws(jws, public_key)
    assert ok, "verify_jws must return True for a valid signature"


def test_tampered_payload_fails_verification() -> None:
    signing_key = Ed25519PrivateKey.generate()
    public_key = signing_key.public_key()

    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)
    parts = jws.split(".")
    # Flip the first character of the payload segment.
    first_char = parts[1][0]
    flipped_char = "B" if first_char == "A" else "A"
    parts[1] = flipped_char + parts[1][1:]
    tampered_jws = f"{parts[0]}.{parts[1]}.{parts[2]}"

    ok = verify_jws(tampered_jws, public_key)
    assert ok is False, "verify_jws must return False for a tampered payload"


def test_rejection_of_a_clearly_malformed_jws() -> None:
    signing_key = Ed25519PrivateKey.generate()
    public_key = signing_key.public_key()

    with pytest.raises(MalformedJws):
        verify_jws("not.a.jws.at.all", public_key)


def test_header_declares_the_rfc9864_algorithm() -> None:
    signing_key = Ed25519PrivateKey.generate()
    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)

    header = json.loads(base64.urlsafe_b64decode(jws.split(".")[0] + "=="))

    assert header == {"alg": "Ed25519", "typ": "VC+LD-JSON+JWS"}


@pytest.mark.parametrize("alg", ["none", "HS256", "RS256", "EdDSA"])
def test_only_the_ed25519_algorithm_is_accepted(alg: str) -> None:
    """
    The registry is an allowlist, checked before any signature verification.

    ``EdDSA`` is included deliberately: RFC 9864 deprecates it, and this
    service does not accept it, so credentials issued before the switch no
    longer verify.
    """
    signing_key = Ed25519PrivateKey.generate()
    header = _b64u(json.dumps({"alg": alg, "typ": "VC+LD-JSON+JWS"}).encode())
    payload = _b64u(json.dumps({"issuer": _KNOWN_DID_KEY}).encode())
    signature = _b64u(signing_key.sign(f"{header}.{payload}".encode("ascii")))

    with pytest.raises(MalformedJws):
        verify_jws(f"{header}.{payload}.{signature}", signing_key.public_key())


def test_payload_shape_includes_context_type_issuer_validfrom_subject() -> None:
    """Validate the W3C VC JSON-LD structure."""
    signing_key = Ed25519PrivateKey.generate()
    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)
    payload = decode_payload(jws)
    assert payload["@context"] == ["https://www.w3.org/ns/credentials/v2"]
    assert payload["type"] == ["VerifiableCredential", "AttestationOfVeracity"]
    assert payload["issuer"] == _KNOWN_DID_KEY
    assert payload["validFrom"] == "2024-01-01T00:00:00Z"
    sub = payload["credentialSubject"]
    assert sub["vc_id"] == "urn:uuid:11111111-2222-3333-4444-555555555555"
    assert sub["valid_since"] == "2024-01-01T00:00:00Z"
    assert sub["subject"] == "did:web:data-consumer.example"
    assert sub["issuer_id"] == "did:web:data-provider.example"
    assert sub["record_id"] == "rec-0001"
    assert sub["contract_id"] == "contract-0001"
    assert sub["data_exchange_id"] == "xchg-0001"
    assert sub["payload"] == "checksum:sha256:abcdef0123456789"
