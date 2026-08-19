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

The migration is not finished: `dva-api` still carries its own `PgVLARepo` and VLA
routes, and nothing calls this service yet.

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

## Run in docker-compose

Not yet wired into `test-env/compose.yml`. The `Dockerfile` builds and runs standalone,
and expects the spec mounted at `/app/openapi.yaml` (see `VLA_MANAGER_OPENAPI_FILE`).

## Configuration (.env)

| Var | Default | Purpose |
|---|---|---|
| `VLA_MANAGER_DB_URL` | *(empty)* | Postgres DSN, e.g. `postgresql://vla:vla@postgres:5432/vla`. Empty → non-persistent in-memory repositories. |
| `VLA_MANAGER_OPENAPI_FILE` | `/app/openapi.yaml` | Hand-written spec served at `/swagger`. Missing → FastAPI's generated schema. |
| `VLA_MANAGER_API_HOST` | `0.0.0.0` | Listen address |
| `VLA_MANAGER_API_PORT` | `8000` | Listen port |
| `VLA_MANAGER_API_LOG_LEVEL` | `info` | One of `critical`, `error`, `warning`, `info`, `debug` |
