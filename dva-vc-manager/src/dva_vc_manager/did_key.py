"""
``did:key`` codec for Ed25519 keys.

The multibase/multicodec encoding is delegated to ``multiformats``; this
module only adds the ``did:key:`` scheme and the Ed25519 constraints.

Reference:
- https://w3c-ccg.github.io/did-method-key/
- The known test vector ``did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK``
"""

from __future__ import annotations

from multiformats import multibase, multicodec
from nacl.signing import VerifyKey

ED25519_RAW_SIZE = 32
ED25519_MULTICODEC = "ed25519-pub"
MULTIBASE_BASE58BTC = "base58btc"
DID_KEY_SCHEME = "did:key:"


def public_key_to_did_key(public_key: VerifyKey) -> str:
    """Encode a PyNaCl Ed25519 VerifyKey into a ``did:key`` identifier."""
    raw = bytes(public_key)
    # multicodec.wrap does not check the payload length for us.
    if len(raw) != ED25519_RAW_SIZE:
        raise ValueError(f"Ed25519 public key must be exactly 32 bytes, got {len(raw)}")
    wrapped = multicodec.wrap(ED25519_MULTICODEC, raw)
    return DID_KEY_SCHEME + multibase.encode(wrapped, MULTIBASE_BASE58BTC)


def did_key_to_public_key(did_key: str) -> VerifyKey:
    """Decode a ``did:key`` Ed25519 identifier back into a PyNaCl VerifyKey."""
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

    return VerifyKey(raw)
