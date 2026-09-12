"""
Ed25519 signing-key store.

Persistence format: base64 of the 32-byte private seed, encoded with
PyNaCl's own codec.  The public key is *derived* from the seed, so a
``SigningKey`` is the whole keypair and only the seed is written to disk.

POSIX file permissions 0600 are applied to the key file, and 0700 to
parent directories.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .did_key import public_key_to_did_key

__all__ = ["SigningKeyStore"]


class SigningKeyStore:
    """Persistent Ed25519 signing key backed by a filesystem path."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._cached: Ed25519PrivateKey | None = None

    @property
    def path(self) -> Path:
        """The key file backing this store."""
        return self._path

    def load_or_generate(self) -> Ed25519PrivateKey:
        """Return the cached key, load it from disk, or generate and persist one."""
        if self._cached is None:
            self._cached = (
                self._load() if self._path.exists() else self._generate_and_persist()
            )
        return self._cached

    def _load(self) -> Ed25519PrivateKey:
        try:
            # validate=True so a stray character is an error rather than being
            # silently discarded, which is base64's default behaviour.
            seed = base64.b64decode(self._path.read_bytes().strip(), validate=True)
            return Ed25519PrivateKey.from_private_bytes(seed)
        except (ValueError, TypeError) as e:
            raise RuntimeError(
                f"Signing key file at {self._path} is malformed ({e}). Expected "
                "base64 of the 32-byte Ed25519 seed. Delete the file to generate "
                "a fresh key -- note that this changes the issuer did:key, which "
                "must then be re-registered with every verifying participant."
            ) from e

    def _generate_and_persist(self) -> Ed25519PrivateKey:
        signing_key = Ed25519PrivateKey.generate()

        # A directory we create is ours, so lock it down; one the operator
        # already provided is left as we found it.
        parent = self._path.parent or Path(".")
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Open with 0600 up front rather than chmod-ing afterwards, so the
        # seed is never briefly readable by other users.
        fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(base64.b64encode(signing_key.private_bytes_raw()))

        return signing_key

    def issuer_did_key(self) -> str:
        """Return the ``did:key`` identifier of the loaded public key."""
        if self._cached is None:
            raise RuntimeError(
                "SigningKeyStore.load_or_generate() must be called before issuer_did_key()"
            )
        return public_key_to_did_key(self._cached.public_key())
