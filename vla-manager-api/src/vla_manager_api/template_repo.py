"""
Template repository — pluggable persistence for VLA Templates.

Ported from the deleted Kotlin ``PgTemplateRepo.kt`` (commit ba876ff~1).
The PostgreSQL implementation owns two tables in a 1:1 relationship,
``templates`` and ``evaluation_methods``; columns mirror the deleted
Kotlin ``templateMapping.kt``.

As with :mod:`vla_manager_api.vla_repo`, the interface is async because
the production path uses asyncpg; the fake returns plain values for ease
of testing.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4


class TemplateRepo(Protocol):
    """Minimal contract for Template persistence."""

    async def all(self) -> list[dict[str, Any]]: ...

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]: ...

    async def add(self, template: dict[str, Any]) -> Optional[UUID]: ...

    async def update(
        self, id: UUID, patch: dict[str, Any]
    ) -> Optional[dict[str, Any]]: ...

    async def remove(self, id: UUID) -> bool: ...

    async def remove_all(self) -> None: ...


class FakeTemplateRepo:
    """In-memory Template repository for tests."""

    def __init__(self) -> None:
        self._templates: dict[UUID, dict[str, Any]] = {}

    async def all(self) -> list[dict[str, Any]]:
        # Inject id into returned dict (mirror PgTemplateRepo behaviour)
        return [{**t, "id": str(tid)} for tid, t in self._templates.items()]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        t = self._templates.get(id)
        return {**t, "id": str(id)} if t is not None else None

    async def add(self, template: dict[str, Any]) -> Optional[UUID]:
        raw_id = template.get("id")
        if raw_id is not None:
            id = UUID(str(raw_id))
        else:
            id = uuid4()
        stored = {k: v for k, v in template.items() if k != "id"}
        self._templates[id] = stored
        return id

    async def update(self, id: UUID, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
        existing = self._templates.get(id)
        if existing is None:
            return None
        for k, v in patch.items():
            if v is not None:
                existing[k] = v
        return {**existing, "id": str(id)}

    async def remove(self, id: UUID) -> bool:
        return self._templates.pop(id, None) is not None

    async def remove_all(self) -> None:
        self._templates.clear()


class PgTemplateRepo:
    """Async-backed PostgreSQL Template repository using asyncpg.

    Owns the ``templates`` + ``evaluation_methods`` tables (1:1).
    Constructed with an ``asyncpg.Pool`` (see
    :mod:`vla_manager_api.dependencies` for pool creation).
    """

    def __init__(self, pool):  # type: ignore[no-untyped-def]
        self._pool = pool

    async def ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_methods (
                    id                     UUID PRIMARY KEY,
                    engine                 VARCHAR(255) NOT NULL,
                    variable_schema        TEXT NOT NULL,
                    implementation_template TEXT NOT NULL
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    id                  UUID PRIMARY KEY,
                    name                VARCHAR(255) NOT NULL,
                    description         TEXT,
                    criterion_type      VARCHAR(255) NOT NULL,
                    target_aspect       VARCHAR(255) NOT NULL,
                    evaluation_method_id UUID NOT NULL
                        REFERENCES evaluation_methods(id) ON DELETE CASCADE
                )
                """
            )

    def _row_to_dict(self, row) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "criterionType": row["criterion_type"],
            "targetAspect": row["target_aspect"],
            "evaluationMethod": {
                "engine": row["engine"],
                "variableSchema": json.loads(row["variable_schema"]),
                "implementationTemplate": row["implementation_template"],
            },
        }

    async def all(self) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT t.id, t.name, t.description, t.criterion_type,
                       t.target_aspect, em.engine, em.variable_schema,
                       em.implementation_template
                FROM templates t
                JOIN evaluation_methods em ON t.evaluation_method_id = em.id
                """
            )
        return [self._row_to_dict(r) for r in rows]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT t.id, t.name, t.description, t.criterion_type,
                       t.target_aspect, em.engine, em.variable_schema,
                       em.implementation_template
                FROM templates t
                JOIN evaluation_methods em ON t.evaluation_method_id = em.id
                WHERE t.id = $1
                """,
                id,
            )
        return self._row_to_dict(row) if row is not None else None

    async def add(self, template: dict[str, Any]) -> Optional[UUID]:
        em = template["evaluationMethod"]
        em_id = uuid4()
        t_id = uuid4()
        async with self._pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """
                INSERT INTO evaluation_methods
                    (id, engine, variable_schema, implementation_template)
                VALUES ($1, $2, $3, $4)
                """,
                em_id,
                em["engine"],
                json.dumps(em["variableSchema"]),
                em["implementationTemplate"],
            )
            await conn.execute(
                """
                INSERT INTO templates
                    (id, name, description, criterion_type, target_aspect,
                     evaluation_method_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                t_id,
                template["name"],
                template.get("description"),
                template["criterionType"],
                template["targetAspect"],
                em_id,
            )
        return t_id

    async def update(self, id: UUID, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Apply a partial update. ``COALESCE`` leaves a column untouched when
        its parameter is NULL, so absent patch keys need no branching.
        """
        em_patch = patch.get("evaluationMethod")
        async with self._pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                "SELECT evaluation_method_id FROM templates WHERE id = $1", id
            )
            if row is None:
                return None

            await conn.execute(
                """
                UPDATE templates
                   SET name           = COALESCE($2::text, name),
                       description    = COALESCE($3::text, description),
                       criterion_type = COALESCE($4::text, criterion_type),
                       target_aspect  = COALESCE($5::text, target_aspect)
                 WHERE id = $1
                """,
                id,
                patch.get("name"),
                patch.get("description"),
                patch.get("criterionType"),
                patch.get("targetAspect"),
            )
            if em_patch is not None:
                await conn.execute(
                    """
                    UPDATE evaluation_methods
                       SET engine                  = COALESCE($2::text, engine),
                           variable_schema         = COALESCE($3::text,
                                                              variable_schema),
                           implementation_template = COALESCE($4::text,
                                                              implementation_template)
                     WHERE id = $1
                    """,
                    row["evaluation_method_id"],
                    em_patch.get("engine"),
                    json.dumps(em_patch["variableSchema"])
                    if em_patch.get("variableSchema") is not None
                    else None,
                    em_patch.get("implementationTemplate"),
                )
        return await self.by_id(id)

    async def remove(self, id: UUID) -> bool:
        async with self._pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                "SELECT evaluation_method_id FROM templates WHERE id = $1", id
            )
            if row is None:
                return False
            await conn.execute("DELETE FROM templates WHERE id = $1", id)
            await conn.execute(
                "DELETE FROM evaluation_methods WHERE id = $1",
                row["evaluation_method_id"],
            )
        return True

    async def remove_all(self) -> None:
        async with self._pool.acquire() as conn, conn.transaction():
            await conn.execute("DELETE FROM templates")
            await conn.execute("DELETE FROM evaluation_methods")
