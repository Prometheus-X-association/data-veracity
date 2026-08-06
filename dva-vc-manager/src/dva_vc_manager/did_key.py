"""
``did:key`` codec for Ed25519 keys.

The multibase/multicodec encoding is delegated to ``multiformats``; this
module only adds the ``did:key:`` scheme and the Ed25519 constraints.

Reference:
- https://w3c-ccg.github.io/did-method-key/
- The known test vector ``did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK``
"""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from multiformats import multibase, multicodec

ED25519_RAW_SIZE = 32
ED25519_MULTICODEC = "ed25519-pub"
MULTIBASE_BASE58BTC = "base58btc"
DID_KEY_SCHEME = "did:key:"


def public_key_to_did_key(public_key: Ed25519PublicKey) -> str:
    """Encode an Ed25519 public key into a ``did:key`` identifier."""
    raw = public_key.public_bytes_raw()
    # multicodec.wrap does not check the payload length for us.
    if len(raw) != ED25519_RAW_SIZE:
        raise ValueError(f"Ed25519 public key must be exactly 32 bytes, got {len(raw)}")
    wrapped = multicodec.wrap(ED25519_MULTICODEC, raw)
    return DID_KEY_SCHEME + multibase.encode(wrapped, MULTIBASE_BASE58BTC)


def did_key_to_public_key(did_key: str) -> Ed25519PublicKey:
    """Decode a ``did:key`` Ed25519 identifier back into an Ed25519 public key."""
    if not did_key.startswith(DID_KEY_SCHEME):
        raise ValueError(f"not a did:key identifier: {did_key}")

    try:
        base, decoded = multibase.decode_raw(did_key.removeprefix(DID_KEY_SCHEME))
        codec, raw = multicodec.unwrap(decoded)
    except KeyError as e:
        # multiformats reports unknown multibase/multicodec prefixes with
        # KeyError subclasses; callers here expect malformed input to raise
        # ValueError, as everything else in this module does.
        raise ValueError(f"unsupported did:key encoding: {did_key}") from e

    if base.name != MULTIBASE_BASE58BTC:
        raise ValueError(f"did:key must use base58btc multibase, got {base.name}")
    if codec.name != ED25519_MULTICODEC:
        raise ValueError(f"did:key must be {ED25519_MULTICODEC}, got {codec.name}")

    return Ed25519PublicKey.from_public_bytes(raw)
