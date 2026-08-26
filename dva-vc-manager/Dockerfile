FROM python:3.12-slim AS build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

# Set working directory
WORKDIR /app/

# Install dependencies
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./dva-vc-manager/uv.lock,target=uv.lock \
    --mount=type=bind,source=./dva-vc-manager/pyproject.toml,target=pyproject.toml \
    uv sync \
	--frozen \
	--no-install-project \
	--no-dev \
	--compile-bytecode \
	--no-editable

# Copy app files
COPY ./dva-vc-manager/ /app/

# Sync project
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --frozen \
	--no-dev \
	--compile-bytecode \
	--no-editable

# ----------------------------------------------------------------
FROM python:3.12-slim

# Install netcat for healthcheck
RUN apt-get update && \
    apt-get install -y \
        --no-install-recommends \
    netcat-openbsd=1.* \
    && rm -rf /var/lib/apt/lists/

# Copy built project
COPY --from=build /app/.venv/ /app/.venv/

# Hand-written OpenAPI spec -- served at /swagger/openapi.json
COPY ./docs/spec/dva-vc-manager.yaml /app/openapi.yaml

ENV DVA_VC_MANAGER_OPENAPI_FILE=/app/openapi.yaml \
    PYTHONUNBUFFERED=1

# Run app; host, port and log level all come from the environment
ENTRYPOINT ["/app/.venv/bin/dva-vc-manager"]

EXPOSE 8000/tcp
