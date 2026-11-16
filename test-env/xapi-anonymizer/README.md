# xAPI anonymizer

A small HTTP service that receives xAPI statements, removes the personal data about students, saves the result and forwards it to the next service.

## What it does

For each statement:

- The student's name is removed.
- The student identifier (`account`, `mbox`, `mbox_sha1sum` or `openid`) is replaced with a hash-like code (HMAC-SHA256). A student keeps the same code within one request. Codes are different in every request.
- `context.instructor`, `context.team` and `authority` are removed.
- The statement `id` is replaced with a new random UUID.
- All other fields stay unchanged.

Before saving, the service checks the output for any original name or identifier. If it finds one, nothing is saved or forwarded.

The result is saved to `output/anonymized_<UTC time>_<random>.json`. If `NEXT_URL` is set, the same data is also POSTed to that address.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8001
```

Or with Docker:

```bash
docker compose up --build -d
```

Optional: set `NEXT_URL` to forward the anonymized statements to another service:

```bash
NEXT_URL=http://localhost:8002/api/statements .venv/bin/uvicorn app.main:app --port 8001
```

## API

### `POST /api/anonymize`

Anonymizes the statements immediately and returns them in the response. Nothing is saved or forwarded. The body is a JSON list of xAPI statements.

```bash
curl -X POST "http://127.0.0.1:8001/api/anonymize" \
  -H "content-type: application/json" \
  -d @statements.json
```

`200 OK` returns the anonymized statements as a JSON list:

```json
[
  {
    "id": "b6f1d1c2-6a0e-4d55-8c1f-2f4b9e0a7d33",
    "actor": {
      "objectType": "Agent",
      "account": { "homePage": "https://anonymizer.example.edu", "name": "3f9a1c0e7b52d8e4...c8b7" }
    },
    "verb": { "id": "http://adlnet.gov/expapi/verbs/failed" },
    "object": { "id": "https://example.edu/xapi/course/lab/1" }
  }
]
```

Errors: `400` if the body is not a JSON list of objects; `422` if a statement has no actor identifier, or if an original name or identifier would still appear in the output (the data is then not returned).

### `POST /api/statements`

Anonymizes the statements in the background, saves the result to `output/` and forwards it to `NEXT_URL` (if set). The body is the same JSON list as above. The optional query parameter `transfer_id` labels the request in the response and logs.

```bash
curl -X POST "http://127.0.0.1:8001/api/statements?transfer_id=batch-01" \
  -H "content-type: application/json" \
  -d @statements.json
```

The service answers right away with `202 Accepted`, before processing starts:

```json
{
  "status": "accepted",
  "transfer_id": "batch-01",
  "output_file": "anonymized_20261112T153012Z_a1b2c3d4.json",
  "received": 36
}
```

If the body is not a JSON list of objects, the response is `400 Bad Request`:

```json
{ "status": "rejected", "reason": "body must be a JSON list of xAPI statements" }
```

### `GET /health`

Returns `{ "status": "ok" }`.

Interactive API docs are available at `http://127.0.0.1:8001/docs` while the service is running.
