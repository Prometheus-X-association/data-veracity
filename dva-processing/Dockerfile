FROM python:3.12-slim AS build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

# Set working directory
WORKDIR /app/

# Install dependencies
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./dva-processing/uv.lock,target=uv.lock \
    --mount=type=bind,source=./dva-processing/pyproject.toml,target=pyproject.toml \
    uv sync \
        --frozen \
	--no-install-project \
	--compile-bytecode \
	--no-editable

# Copy app files
COPY ./dva-processing/ /app/

# Sync project
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --frozen \
	--compile-bytecode \
	--no-editable

# ----------------------------------------------------------------
FROM python:3.12-slim

# Copy built project
COPY --from=build --chown=app:app /app/.venv/ /app/.venv/

COPY ./docs/spec/dva-processing.yaml /app/openapi.yaml
COPY ./docs/spec/components.yaml /app/components.yaml

ENV DVA_PROCESSING_OPENAPI_FILE=/app/openapi.yaml

# Run app
ENTRYPOINT ["/app/.venv/bin/dva-processing"]

EXPOSE 5000/tcp

# Liveness only: /readyz probes dependencies, and an outage elsewhere must not
# get this container marked unhealthy.  See docs/health-checks.md.
HEALTHCHECK --interval=5s --timeout=5s --retries=5 \
    CMD python3 -c "import urllib.request as r; r.urlopen('http://localhost:5000/livez', timeout=4)"
