# VLA Manager API

VLA Manager API is a FastAPI service hosted at the **Data Intermediary** that owns
Veracity Level Agreements (VLAs) and the templates used to build them, on behalf of all
participants.

## Why

The goal of the refactored DVA topology is for this to be the **only** place VLAs live.
Rather than each participant's DVA API keeping VLAs in its own Postgres, the DVA API
resolves a VLA by calling `GET /vla/{id}` over HTTP on this service during the
synchronous attestation flow.

Separating VLA ownership from the attestation gateway means:
- DVA API shrinks to pure orchestration (HTTP gateway; one role)
- VLAs are authored once and shared across participants
- The VLA Manager Vue UI talks to a single dedicated backend

`dva-api`'s own VLA routes and `PgVLARepo` are gone, and `dva-processing` resolves
templates by calling `GET /template/{id}` here.  What is left of the migration is
deployment: this service is not yet in `test-env/compose.yml`.

## Role

| Endpoint | Persona | Purpose |
|---|---|---|
| `GET /vla` | VLA Manager UI, admin | List all VLAs |
| `GET /vla/{id}` | DVA API, UI | Retrieve a VLA by its UUID — used during VLA resolution in the synchronous attestation flow |
| `POST /vla` | VLA Manager UI | Create a VLA from a partial ODCS payload |
| `POST /vla/from-templates` | VLA Manager UI | Create a VLA by rendering templates and merging the results into its `quality` array |
| `DELETE /vla` | Admin only | Wipe all VLAs |
| `GET /template` | VLA Manager UI | List all VLA templates |
| `GET /template/{id}` | VLA Manager UI | Retrieve a template by its UUID |
| `POST /template` | VLA Manager UI | Create a template |
| `PATCH /template/{id}` | VLA Manager UI | Partially update a template; body `id` must match the path |
| `DELETE /template/{id}` | VLA Manager UI | Delete one template |
| `DELETE /template` | Admin only | Wipe all templates |
| `POST /template/{id}/render` | VLA Manager UI | Render a template's `implementationTemplate` with a model |
| `POST /template/{id}/validate` | VLA Manager UI | Render a template with a model and have DVA Processing check that the logic compiles |
| `POST /assistant/template` | VLA Manager UI | Generate an unsaved template draft from a natural-language request |

This service intentionally does **not** do evaluation, attestation, or credential issuance —
those are concerns of `dva-processing` and the `dva-vc-manager` respectively.

The hand-written OpenAPI spec lives at [`docs/spec/vla-manager-api.yaml`](../docs/spec/vla-manager-api.yaml)
and is served at `/swagger` (Swagger UI) and `/redoc`, with the schema itself at
`/swagger/openapi.json`.

## Run locally (dev)

```bash
cd data-veracity/vla-manager-api
uv sync
uv run pytest                # tests (in-memory repos, no Postgres needed)
uv run vla-manager-api       # boot the service on :8000
```

With `VLA_MANAGER_DB_URL` unset the service boots against in-memory repositories so it
runs without a Postgres; state is lost on restart, so set the DSN for any deployment.

## Health

`GET /livez` always passes; `GET /readyz` fails when Postgres does not answer, and warns when `VLA_MANAGER_DB_URL` is not set.
See [`docs/health-checks.md`](../docs/health-checks.md).

## Run in docker-compose

Not yet wired into `test-env/compose.yml`. The `Dockerfile` builds and runs standalone,
and expects the spec mounted at `/app/openapi.yaml` (see `VLA_MANAGER_OPENAPI_FILE`).
The spec `$ref`s the schemas shared across the DVA components, so mount
`docs/spec/components.yaml` alongside it at `/app/components.yaml`; it is served at
`/swagger/components.yaml`, which is where those references resolve to.  Without it the
spec is still served and `/swagger/components.yaml` answers `404`.

## Configuration (.env)

| Var | Default | Purpose |
|---|---|---|
| `VLA_MANAGER_DB_URL` | *(empty)* | Postgres DSN, e.g. `postgresql://vla:vla@postgres:5432/vla`. Empty → non-persistent in-memory repositories. |
| `VLA_MANAGER_OPENAPI_FILE` | `/app/openapi.yaml` | Hand-written spec served at `/swagger`. Missing → FastAPI's generated schema. `components.yaml` next to it is served at `/swagger/components.yaml`, where the spec's `$ref`s point. |
| `VLA_MANAGER_API_HOST` | `0.0.0.0` | Listen address |
| `VLA_MANAGER_API_PORT` | `8000` | Listen port |
| `VLA_MANAGER_API_LOG_LEVEL` | `info` | One of `critical`, `error`, `warning`, `info`, `debug`. At `debug`, every request to the assistant service is logged with its URL, headers (credentials redacted) and full body, and every response with its status, headers, body and latency – prompts and model output included. |
| `VLA_MANAGER_API_LOG_FORMAT` | `auto` | `json` for one JSON object per line, `console` for human-readable output, or `auto` to pick `console` on a TTY and `json` otherwise. Covers uvicorn's own logs too. Each event carries the `request_id` of the HTTP request that caused it (the caller's `X-Request-ID`, or a generated one echoed back in that header). |
| `VLA_MANAGER_API_PROCESSING_URL` | `http://localhost:5000` | URL to a DVA processing instance |
| `VLA_MANAGER_AI_PROVIDER` | `openai` | `openai` for OpenAI-compatible services, `gemini` for Gemini's compatibility endpoint, `openrouter` for OpenRouter, or `anthropic` for the native Messages API |
| `VLA_MANAGER_AI_URL` | *(empty)* | Provider base URL or complete endpoint URL. Defaults to the provider's public endpoint. Empty credentials disable the assistant. |
| `VLA_MANAGER_AI_API_KEY` | *(empty)* | API key used only by the VLA Manager API. |
| `VLA_MANAGER_AI_MODEL` | *(empty)* | Model name sent to the assistant service. Gemini defaults to `gemini-3.5-flash-lite`; other providers require an explicit model. |
| `VLA_MANAGER_AI_TIMEOUT_SECONDS` | `30` | Maximum assistant request duration. |

The assistant returns a structured draft and never saves a template. The UI must show the
draft for review and use the normal template validation and save actions afterward. Do not
place the API key in frontend environment variables or browser code.

Example provider settings:

```console
# Gemini
VLA_MANAGER_AI_PROVIDER=gemini
VLA_MANAGER_AI_API_KEY=your-gemini-key

# OpenAI or another OpenAI-compatible gateway
VLA_MANAGER_AI_PROVIDER=openai
VLA_MANAGER_AI_URL=https://api.openai.com/v1
VLA_MANAGER_AI_API_KEY=your-openai-key
VLA_MANAGER_AI_MODEL=your-model

# OpenRouter
VLA_MANAGER_AI_PROVIDER=openrouter
VLA_MANAGER_AI_API_KEY=your-openrouter-key
VLA_MANAGER_AI_MODEL=vendor/model

# Anthropic
VLA_MANAGER_AI_PROVIDER=anthropic
VLA_MANAGER_AI_URL=https://api.anthropic.com/v1
VLA_MANAGER_AI_API_KEY=your-anthropic-key
VLA_MANAGER_AI_MODEL=your-model
```
