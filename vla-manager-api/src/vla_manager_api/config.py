"""Runtime configuration for the VLA Manager API."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["critical", "error", "warning", "info", "debug"]
AIProvider = Literal["openai", "gemini", "anthropic"]


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

    # Optional chat completion service used by the template assistant.
    # Empty credentials disable the assistant cleanly.
    ai_provider: AIProvider = Field(
        "openai", validation_alias="VLA_MANAGER_AI_PROVIDER"
    )
    ai_url: str = Field("", validation_alias="VLA_MANAGER_AI_URL")
    ai_api_key: str = Field("", validation_alias="VLA_MANAGER_AI_API_KEY")
    ai_model: str = Field("", validation_alias="VLA_MANAGER_AI_MODEL")
    ai_timeout_seconds: float = Field(
        30.0, validation_alias="VLA_MANAGER_AI_TIMEOUT_SECONDS"
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
