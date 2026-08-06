"""did:key codec round-trip tests."""

from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from multiformats import multibase, multicodec

from dva_vc_manager.did_key import (
    did_key_to_public_key,
    public_key_to_did_key,
)


def test_ed25519_key_round_trips_through_did_key() -> None:
    signing_key = Ed25519PrivateKey.generate()
    pub = signing_key.public_key()

    did_key = public_key_to_did_key(pub)
    round_tripped_pub = did_key_to_public_key(did_key)
    round_tripped_did_key = public_key_to_did_key(round_tripped_pub)

    assert did_key == round_tripped_did_key, (
        "did:key round-trip must produce the same identifier"
    )


def test_known_spec_vector() -> None:
    expected = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    pub = did_key_to_public_key(expected)
    reencoded = public_key_to_did_key(pub)
    assert reencoded == expected


def test_starts_with_did_key_z6mk() -> None:
    signing_key = Ed25519PrivateKey.generate()
    pub = signing_key.public_key()
    did_key = public_key_to_did_key(pub)
    assert did_key.startswith("did:key:z6Mk"), (
        "did:key identifier must start with 'did:key:z6Mk'"
    )


def _did_key(codec: str, base: str = "base58btc", raw: bytes | None = None) -> str:
    raw = (
        raw
        if raw is not None
        else Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    )
    return "did:key:" + multibase.encode(multicodec.wrap(codec, raw), base)


@pytest.mark.parametrize(
    "bad_did_key",
    [
        pytest.param("did:web:example.com", id="not_a_did_key"),
        pytest.param("did:key:", id="empty"),
        pytest.param("did:key:Q6MkhaXgBZDvotDkL5257fai", id="unknown_multibase"),
        pytest.param("did:key:z6MkO0Il", id="invalid_base58_chars"),
        pytest.param(_did_key("ed25519-pub", base="base16"), id="not_base58btc"),
        pytest.param(_did_key("x25519-pub"), id="x25519_not_ed25519"),
        pytest.param(_did_key("secp256k1-pub"), id="secp256k1_not_ed25519"),
        pytest.param(_did_key("ed25519-pub", raw=b"short"), id="wrong_key_length"),
    ],
)
def test_malformed_did_key_raises_value_error(bad_did_key: str) -> None:
    """
    Malformed input must raise ValueError, never KeyError.

    ``multiformats`` signals unknown multibase/multicodec prefixes with
    KeyError subclasses, which ``aov_verify`` does not catch -- those would
    surface as HTTP 500 rather than ``verified: false``.
    """
    with pytest.raises(ValueError):
        did_key_to_public_key(bad_did_key)
