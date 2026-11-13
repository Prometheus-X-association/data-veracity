FROM python:3.12-slim

# The lock file is in the format of this uv version
RUN pip install --no-cache-dir uv==0.11.18

WORKDIR /app/

# Install the dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --compile-bytecode

COPY main.py ./

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8090
# The service has a single endpoint of its own; FastAPI's OpenAPI document is up when it is
HEALTHCHECK --interval=5s --timeout=2s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/openapi.json', timeout=1)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
