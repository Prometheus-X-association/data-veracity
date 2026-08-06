"""Signing key store tests."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

from dva_vc_manager.keys import SigningKeyStore


def test_generates_key_on_first_run_when_file_missing(tmp_path: Path) -> None:
    key_path = tmp_path / "subdir" / "key.pem"
    store = SigningKeyStore(str(key_path))

    signing_key = store.load_or_generate()

    assert key_path.exists(), "Key file must be created on first run"
    assert len(signing_key.private_bytes_raw()) == 32
    assert signing_key.public_key() is not None
    # Permissions: 0600 on the key, 0700 on a directory we created.
    if os.name == "posix":
        assert (key_path.stat().st_mode & 0o777) == 0o600
        assert (key_path.parent.stat().st_mode & 0o777) == 0o700


def test_persists_and_reloads_the_same_key_across_instances(tmp_path: Path) -> None:
    key_path = tmp_path / "key.pem"

    store1 = SigningKeyStore(str(key_path))
    key1 = store1.load_or_generate()

    # New instance pointing at the same file — must load, not regenerate.
    store2 = SigningKeyStore(str(key_path))
    key2 = store2.load_or_generate()

    assert (
        key1.public_key().public_bytes_raw() == key2.public_key().public_bytes_raw()
    ), "reload must yield the same public key as the original generation"
    assert key1.private_bytes_raw() == key2.private_bytes_raw(), (
        "reload must yield the same private seed"
    )


def test_stores_only_the_seed_not_the_public_key(tmp_path: Path) -> None:
    """The public key is derived from the seed, so it is not persisted."""
    key_path = tmp_path / "key.pem"
    signing_key = SigningKeyStore(str(key_path)).load_or_generate()

    contents = key_path.read_bytes()
    assert b"|" not in contents, "legacy seed|public separator must be gone"
    assert base64.b64decode(contents) == signing_key.private_bytes_raw()
    assert len(base64.b64decode(contents)) == 32


def test_malformed_key_file_raises_rather_than_regenerating(tmp_path: Path) -> None:
    """A corrupt key file must fail loudly, never mint a new issuer did:key."""
    key_path = tmp_path / "key.pem"
    key_path.write_text("not base64 at all!")

    with pytest.raises(RuntimeError, match="malformed"):
        SigningKeyStore(str(key_path)).load_or_generate()


def test_derived_did_key_starts_with_z6mk(tmp_path: Path) -> None:
    store = SigningKeyStore(str(tmp_path / "key.pem"))
    store.load_or_generate()
    did_key = store.issuer_did_key()
    assert did_key.startswith("did:key:z6Mk")
