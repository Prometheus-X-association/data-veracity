"""Credential and verification audit persistence.

The audit log intentionally stores the complete request and response bodies.
It is append-only: issued credentials and verification attempts are never
updated or deleted by the service.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

import asyncpg
from pydantic import BaseModel

__all__ = ["AuditRepo", "CredentialAudit", "VerificationAudit", "FakeAudit", "PgAudit"]


class CredentialAudit(BaseModel):
    id: UUID
    credential_id: str
    jws: str
    request: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "CredentialAudit":
        return cls(
            id=row["id"],
            credential_id=row["credential_id"],
            jws=row["jws"],
            request=_json_value(row["request"]),
            created_at=row["created_at"],
        )


class VerificationAudit(BaseModel):
    id: UUID
    request: dict[str, Any]
    response: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "VerificationAudit":
        return cls(
            id=row["id"],
            request=_json_value(row["request"]),
            response=_json_value(row["response"]),
            created_at=row["created_at"],
        )


def _json_value(value: Any) -> dict[str, Any]:
    return json.loads(value) if isinstance(value, str) else value


class AuditRepo(Protocol):
    async def record_credential(
        self, credential_id: str, jws: str, request: dict[str, Any]
    ) -> CredentialAudit: ...
    async def record_verification(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> VerificationAudit: ...
    async def credentials(self) -> list[CredentialAudit]: ...
    async def verifications(self) -> list[VerificationAudit]: ...
    async def close(self) -> None: ...


class FakeAudit:
    """In-memory audit store for local development without PostgreSQL."""

    def __init__(self) -> None:
        self._credentials: list[CredentialAudit] = []
        self._verifications: list[VerificationAudit] = []

    async def record_credential(
        self, credential_id: str, jws: str, request: dict[str, Any]
    ) -> CredentialAudit:
        entry = CredentialAudit(
            id=uuid4(), credential_id=credential_id, jws=jws, request=request,
            created_at=datetime.now(timezone.utc),
        )
        self._credentials.append(entry)
        return entry

    async def record_verification(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> VerificationAudit:
        entry = VerificationAudit(
            id=uuid4(), request=request, response=response,
            created_at=datetime.now(timezone.utc),
        )
        self._verifications.append(entry)
        return entry

    async def credentials(self) -> list[CredentialAudit]:
        return list(reversed(self._credentials))

    async def verifications(self) -> list[VerificationAudit]:
        return list(reversed(self._verifications))

    async def close(self) -> None:
        """No-op; nothing to release."""


class PgAudit:
    """PostgreSQL implementation of the append-only credential audit log."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS issued_credentials (
                    id UUID PRIMARY KEY,
                    credential_id TEXT UNIQUE NOT NULL,
                    jws TEXT NOT NULL,
                    request JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS verification_audit_log (
                    id UUID PRIMARY KEY,
                    request JSONB NOT NULL,
                    response JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS verification_audit_log_created_at_idx
                    ON verification_audit_log (created_at DESC);
                """
            )

    async def record_credential(
        self, credential_id: str, jws: str, request: dict[str, Any]
    ) -> CredentialAudit:
        entry_id = uuid4()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO issued_credentials (id, credential_id, jws, request)
                   VALUES ($1, $2, $3, $4::jsonb)
                   RETURNING id, credential_id, jws, request, created_at""",
                entry_id, credential_id, jws, json.dumps(request),
            )
        return CredentialAudit.from_row(row)

    async def record_verification(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> VerificationAudit:
        entry_id = uuid4()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO verification_audit_log (id, request, response)
                   VALUES ($1, $2::jsonb, $3::jsonb)
                   RETURNING id, request, response, created_at""",
                entry_id, json.dumps(request), json.dumps(response),
            )
        return VerificationAudit.from_row(row)

    async def credentials(self) -> list[CredentialAudit]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, credential_id, jws, request, created_at "
                "FROM issued_credentials ORDER BY created_at DESC"
            )
        return [CredentialAudit.from_row(row) for row in rows]

    async def verifications(self) -> list[VerificationAudit]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, request, response, created_at "
                "FROM verification_audit_log ORDER BY created_at DESC"
            )
        return [VerificationAudit.from_row(row) for row in rows]

    async def close(self) -> None:
        """Close the pool owned by this repository."""
        await self._pool.close()
