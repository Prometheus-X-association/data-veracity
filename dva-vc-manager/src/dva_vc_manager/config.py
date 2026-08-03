"""Runtime configuration for the DVA VC Manager."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["critical", "error", "warning", "info", "debug"]


class Config(BaseSettings):
    """
    Settings read from the environment, prefixed ``DVA_VC_MANAGER_``.

    Read at instantiation, so tests can build their own ``Config()``
    against a patched environment.
    """

    model_config = SettingsConfigDict(
        env_prefix="DVA_VC_MANAGER_", populate_by_name=True
    )

    host: str = "0.0.0.0"
    port: int = 8000

    # Both structlog and uvicorn take these names, lowercased.
    log_level: LogLevel = "info"

    # Ed25519 signing key file path.
    # Loaded at startup; created and persisted (0600) if missing.
    signing_key_path: str = "/data/dva-vc-signing-key.pem"

    # Postgres DSN (whitelist); empty → fall back to in-memory FakeWhitelist.
    # Predates the env_prefix convention, hence the explicit alias.
    postgres_dsn: str = Field("", validation_alias="DVA_VC_MANAGER_DB_URL")

    # Hand-written OpenAPI spec served at /swagger.
    # Missing → fall back to FastAPI's auto-generated schema.
    openapi_file: str = "/app/openapi.yaml"

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, value: object) -> object:
        """Accept ``INFO`` as well as ``info``, and ``warn`` for ``warning``."""
        if not isinstance(value, str):
            return value
        value = value.lower()
        return "warning" if value == "warn" else value


cfg = Config()
