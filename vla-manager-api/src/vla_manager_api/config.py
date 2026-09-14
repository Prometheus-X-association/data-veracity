"""Runtime configuration for the VLA Manager API."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["critical", "error", "warning", "info", "debug"]


class Config(BaseSettings):
    """
    Settings read from the environment, prefixed ``VLA_MANAGER_API_``.

    Read at instantiation, so tests can build their own ``Config()``
    against a patched environment.
    """

    model_config = SettingsConfigDict(
        env_prefix="VLA_MANAGER_API_", populate_by_name=True
    )

    host: str = "0.0.0.0"
    port: int = 8000
    processing_url: str = "http://localhost:5000"

    # Both structlog and uvicorn take these names, lowercased.
    log_level: LogLevel = "info"

    # Postgres DSN. Required for the production (asyncpg) repositories.
    # Example: postgresql://vla:vla@postgres-vla:5432/vla
    # Predates the env_prefix convention, hence the explicit alias.
    postgres_dsn: str = Field("", validation_alias="VLA_MANAGER_DB_URL")

    # Hand-written OpenAPI spec served at /swagger.
    # Missing → fall back to FastAPI's auto-generated schema.
    # Predates the env_prefix convention, hence the explicit alias.
    openapi_file: str = Field(
        "/app/openapi.yaml", validation_alias="VLA_MANAGER_OPENAPI_FILE"
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, value: object) -> object:
        """Accept ``INFO`` as well as ``info``, and ``warn`` for ``warning``."""
        if not isinstance(value, str):
            return value
        value = value.lower()
        return "warning" if value == "warn" else value


cfg = Config()
