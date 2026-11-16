"""xAPI aggregation service.

Receives de-identified xAPI statements, aggregates them per student, saves the
result to output/ and forwards it to NEXT_URL (if set). See README.md.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, Query, Request
from fastapi.responses import JSONResponse

# --- Constants (NEXT_URL env var is the only setting) -----------------------
FINAL_RESULT_TYPE = "http://adlnet.gov/expapi/activities/course"
NO_RESULT = "no result"
NO_GRADE = "no grade"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
FORWARD_TIMEOUT_S = 60.0
# Same convention as the anonymizer: an id the caller did not send is made up
# here, and the prefix marks it as not coming from the sender.
GENERATED_ID_PREFIX = "generated-"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("aggregation")

app = FastAPI(title="xAPI aggregation")


# --- Aggregation -------------------------------------------------------------
def _get(node: Any, *keys: str) -> Any:
    """Safe nested dict lookup: _get(st, "actor", "account", "name")."""
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def aggregate(statements: list[dict]) -> tuple[list[dict], int]:
    """Return (per-student rows sorted by student, number of skipped statements)."""
    events: dict[str, int] = {}
    finals: dict[str, dict] = {}
    skipped = 0
    for st in statements:
        student = _get(st, "actor", "account", "name")
        if not isinstance(student, str) or not student.strip():
            skipped += 1
            continue
        events[student] = events.get(student, 0) + 1
        if _get(st, "object", "definition", "type") == FINAL_RESULT_TYPE:
            finals[student] = st  # if a student has several, the last one wins

    rows = []
    for student in sorted(events):
        final = finals.get(student)
        if final is None:
            result, grade = NO_RESULT, NO_GRADE
        else:
            result = _get(final, "verb", "display", "en-US")
            grade = _get(final, "result", "score", "raw")
            if grade is None:  # final result without a score
                grade = NO_GRADE
        rows.append({"name": student, "events": events[student], "result": result, "grade": grade})
    return rows, skipped


# --- Save / forward ----------------------------------------------------------
def output_file_name() -> str:
    """Date-based name, independent of the transfer_id (which may contain any characters)."""
    return f"aggregated_{datetime.now(timezone.utc):%Y-%m-%d_%H-%M-%S}_{uuid.uuid4().hex[:8]}.json"


def save_output(file_name: str, rows: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / file_name
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def forward(transfer_id: str, rows: list[dict]) -> None:
    next_url = os.environ.get("NEXT_URL", "").strip()
    if not next_url:
        log.info("transfer_id=%s forward=skipped reason=NEXT_URL_not_set", transfer_id)
        return
    try:
        with httpx.Client(timeout=FORWARD_TIMEOUT_S) as client:
            resp = client.post(next_url, json=rows)  # same bare array as the saved file
        resp.raise_for_status()
        log.info("transfer_id=%s forward=ok http_status=%s students=%d", transfer_id, resp.status_code, len(rows))
    except httpx.HTTPStatusError as exc:
        log.error("transfer_id=%s forward=failed http_status=%s", transfer_id, exc.response.status_code)
    except httpx.HTTPError as exc:
        log.error("transfer_id=%s forward=failed error=%s", transfer_id, type(exc).__name__)


def process(transfer_id: str, statements: list[dict]) -> None:
    """Runs after the 202 receipt has been sent. `transfer_id` must already be log-safe."""
    try:
        rows, skipped = aggregate(statements)
        if skipped:
            log.warning("transfer_id=%s skipped_without_student=%d", transfer_id, skipped)
        file_name = output_file_name()
        save_output(file_name, rows)
        log.info("transfer_id=%s status=saved file=%s statements=%d students=%d",
                 transfer_id, file_name, len(statements) - skipped, len(rows))
    except Exception as exc:  # no traceback: it could contain statement contents
        log.error("transfer_id=%s status=failed error=%s saved=0 forwarded=0", transfer_id, type(exc).__name__)
        return
    forward(transfer_id, rows)


# --- API ---------------------------------------------------------------------
def _bad_request(reason: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"status": "rejected", "reason": reason})


async def _read_statements(request: Request) -> list[dict] | JSONResponse:
    """Parse and check the body: a JSON array of objects, or a 400 response."""
    raw = await request.body()
    try:
        body = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _bad_request("body is not valid JSON")
    if not isinstance(body, list):
        return _bad_request("body must be a JSON array of xAPI statements")
    for i, st in enumerate(body):
        if not isinstance(st, dict):
            return _bad_request(f"statements[{i}] is not a JSON object")
    return body


def _log_safe(value: str) -> str:
    """Escape control characters (newlines etc.) so an id cannot forge log lines."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def resolve_transfer_id(provided: str | None) -> str:
    if provided is None or provided.strip() == "":
        return f"{GENERATED_ID_PREFIX}{uuid.uuid4()}"
    return provided.strip()


# The body is validated by hand (to answer 400, not FastAPI's 422), so it is
# described here only so that /docs shows a request body editor.
STATEMENTS_REQUEST_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {"type": "array", "items": {"type": "object"}},
            "example": [
                {
                    "actor": {"objectType": "Agent",
                              "account": {"homePage": "https://anonymizer.example.edu", "name": "student-001"}},
                    "verb": {"id": "http://adlnet.gov/expapi/verbs/passed", "display": {"en-US": "passed"}},
                    "object": {"objectType": "Activity", "id": "https://example.edu/xapi/course/software-engineering",
                               "definition": {"type": FINAL_RESULT_TYPE}},
                    "result": {"score": {"raw": 3}},
                }
            ],
        }
    },
}


@app.post(
    "/api/statements",
    status_code=202,
    openapi_extra={"requestBody": STATEMENTS_REQUEST_BODY},
    responses={400: {"description": "Body is not a JSON array of statement objects"}},
)
async def receive_statements(
    request: Request,
    background_tasks: BackgroundTasks,
    transfer_id: str | None = Query(
        default=None,
        description="Sender's transfer id. If omitted, a placeholder id starting with 'generated-' is created.",
    ),
):
    body = await _read_statements(request)
    if isinstance(body, JSONResponse):
        return body

    transfer_id = resolve_transfer_id(transfer_id)
    log_id = _log_safe(transfer_id)
    log.info("transfer_id=%s status=accepted received=%d", log_id, len(body))
    background_tasks.add_task(process, log_id, body)
    return {"status": "accepted", "transfer_id": transfer_id, "received": len(body)}


@app.post(
    "/api/aggregate",
    openapi_extra={"requestBody": STATEMENTS_REQUEST_BODY},
    responses={400: {"description": "Body is not a JSON array of statement objects"}},
)
async def aggregate_now(request: Request):
    """Same input as /api/statements, but aggregates right away and returns the rows.
    Nothing is saved or forwarded."""
    body = await _read_statements(request)
    if isinstance(body, JSONResponse):
        return body
    rows, skipped = aggregate(body)
    if skipped:
        log.warning("endpoint=aggregate skipped_without_student=%d", skipped)
    log.info("endpoint=aggregate status=returned statements=%d students=%d", len(body) - skipped, len(rows))
    return rows


@app.get("/health")
async def health():
    return {"status": "ok"}
