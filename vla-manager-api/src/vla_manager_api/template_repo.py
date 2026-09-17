"""
Template repository — pluggable persistence for VLA Templates.

The PostgreSQL implementation owns two tables in a 1:1 relationship,
``templates`` and ``evaluation_methods``.

As with :mod:`vla_manager_api.vla_repo`, the interface is async because
the production path uses asyncpg; the fake returns plain values for ease
of testing.
"""

from __future__ import annotations

import json
from typing import Optional, Protocol
from uuid import UUID, uuid4

from .models import Template, TemplateNew, TemplatePatch


def _apply_patch(existing: Template, patch: TemplatePatch) -> Template:
    """
    Return ``existing`` with the fields ``patch`` sets replaced.

    Re-validated rather than copied field by field, so a patched
    ``evaluationMethod`` comes back as the model and not the dict it was
    dumped to.  ``exclude_none`` is what makes this a partial update: a
    field the caller left out is not a request to clear it.
    """
    return Template.model_validate(
        {
            **existing.model_dump(),
            **patch.model_dump(exclude_none=True, exclude={"id"}),
        }
    )


class TemplateRepo(Protocol):
    """Minimal contract for Template persistence."""

    async def all(self) -> list[Template]: ...

    async def by_id(self, id: UUID) -> Optional[Template]: ...

    async def add(self, template: TemplateNew) -> Optional[UUID]: ...

    async def update(self, id: UUID, patch: TemplatePatch) -> Optional[Template]: ...

    async def remove(self, id: UUID) -> bool: ...

    async def remove_all(self) -> None: ...


class FakeTemplateRepo:
    """In-memory Template repository for tests."""

    def __init__(self) -> None:
        self._templates: dict[UUID, Template] = {}

    async def all(self) -> list[Template]:
        return list(self._templates.values())

    async def by_id(self, id: UUID) -> Optional[Template]:
        return self._templates.get(id)

    async def add(self, template: TemplateNew) -> Optional[UUID]:
        id = uuid4()
        self._templates[id] = Template(id=id, **template.model_dump())
        return id

    async def update(self, id: UUID, patch: TemplatePatch) -> Optional[Template]:
        existing = self._templates.get(id)
        if existing is None:
            return None
        self._templates[id] = _apply_patch(existing, patch)
        return self._templates[id]

    async def remove(self, id: UUID) -> bool:
        return self._templates.pop(id, None) is not None

    async def remove_all(self) -> None:
        self._templates.clear()


class PgTemplateRepo:
    """
    Async-backed PostgreSQL Template repository using asyncpg.

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

    def _row_to_template(self, row) -> Template:  # type: ignore[no-untyped-def]
        return Template.model_validate(
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "criterion_type": row["criterion_type"],
                "target_aspect": row["target_aspect"],
                "evaluation_method": {
                    "engine": row["engine"],
                    "variable_schema": json.loads(row["variable_schema"]),
                    "implementation_template": row["implementation_template"],
                },
            }
        )

    async def all(self) -> list[Template]:
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
        return [self._row_to_template(r) for r in rows]

    async def by_id(self, id: UUID) -> Optional[Template]:
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
        return self._row_to_template(row) if row is not None else None

    async def add(self, template: TemplateNew) -> Optional[UUID]:
        em = template.evaluation_method
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
                # `.value` throughout: the columns are VARCHAR, and asyncpg
                # is handed a plain string rather than an enum member.
                em.engine.value,
                json.dumps(em.variable_schema),
                em.implementation_template,
            )
            await conn.execute(
                """
                INSERT INTO templates
                    (id, name, description, criterion_type, target_aspect,
                     evaluation_method_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                t_id,
                template.name,
                template.description,
                template.criterion_type.value,
                template.target_aspect.value,
                em_id,
            )
        return t_id

    async def update(self, id: UUID, patch: TemplatePatch) -> Optional[Template]:
        """
        Apply a partial update. ``COALESCE`` leaves a column untouched when
        its parameter is NULL, so absent patch fields need no branching.
        """
        em_patch = patch.evaluation_method
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
                patch.name,
                patch.description,
                patch.criterion_type.value if patch.criterion_type else None,
                patch.target_aspect.value if patch.target_aspect else None,
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
                    em_patch.engine.value,
                    json.dumps(em_patch.variable_schema),
                    em_patch.implementation_template,
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
