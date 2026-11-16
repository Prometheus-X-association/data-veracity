# xAPI aggregation

This service is a step in an xAPI data pipeline. It receives de-identified xAPI statements and builds one summary per student: how many statements the student has (`events`) and their final course result and grade. It has no UI and works only over HTTP.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8002
```

Or with Docker: `docker compose up --build -d`.

Optional: set `NEXT_URL` to the endpoint of the next service in the pipeline.

## API

Both POST endpoints take the same body: a JSON array of xAPI statements, for example:

```json
[
  {
    "actor": { "account": { "homePage": "https://anonymizer.example.edu", "name": "student-001" } },
    "verb": { "id": "http://adlnet.gov/expapi/verbs/failed", "display": { "en-US": "failed" } },
    "object": { "id": "https://example.edu/xapi/course/software-engineering",
                "definition": { "type": "http://adlnet.gov/expapi/activities/course" } },
    "result": { "score": { "raw": 1 } }
  }
]
```

If the body is not a JSON array of objects, both return `400 Bad Request`.

### `POST /api/aggregate`

This endpoint aggregates the statements and returns the result directly with `200 OK`. It saves nothing and forwards nothing.

### `POST /api/statements`

This endpoint is for the pipeline. It replies right away with `202 Accepted` and a receipt, then aggregates the statements in the background. It saves the result to `output/` and forwards it to `NEXT_URL` if that is set.

```json
{ "status": "accepted", "transfer_id": "batch-2026-11", "received": 5578 }
```

Optional query parameter: `transfer_id`, which is the sender's id for this transfer.

### `GET /health`

Returns `{ "status": "ok" }`.

## Output

The result has one object per student, sorted by `name`:

```json
[
  { "name": "student-001", "events": 10, "result": "failed",    "grade": 1 },
  { "name": "student-004", "events": 7,  "result": "no result", "grade": "no grade" }
]
```

- `events`: the number of statements from the student.
- `result`: `passed` or `failed`, taken from the final course statement, or `no result` if the student has none.
- `grade`: the score of that final statement, or `no grade` if there is none.
