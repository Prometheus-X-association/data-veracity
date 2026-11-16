"""xAPI anonymizer service.

Receives xAPI statements, de-identifies the student identifiers, saves the
result to output/ and forwards it to NEXT_URL (if set). See README.md.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

# --- Constants (NEXT_URL env var is the only setting) -----------------------
ANON_HOMEPAGE = "https://anonymizer.example.edu"
# Pseudonym = HMAC-SHA256(per-batch random key, original identifier), as hex.
# The key is made fresh for every batch and never stored, so codes cannot be
# reversed or linked between batches (a plain hash of a short Neptun code could
# be reversed by hashing every possible code).
HASH_KEY_BYTES = 32
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
FORWARD_TIMEOUT_S = 60.0
IFI_KEYS = ("account", "mbox", "mbox_sha1sum", "openid")  # xAPI inverse functional identifiers
REMOVED_CONTEXT_KEYS = ("instructor", "team")
# A transfer_id the caller did not send is made up here. The prefix marks it as
# not real (not from the sender) everywhere: receipt, log lines and file name.
GENERATED_ID_PREFIX = "generated-"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("anonymizer")

app = FastAPI(title="xAPI anonymizer")


class AnonymizationError(Exception):
    """Processing must stop. The message must never contain personal data."""


# --- Collecting the original names / identifiers -----------------------------
def _agent_sensitive_values(agent: Any, out: set[str]) -> None:
    """Add every name and identifier value of an xAPI Agent/Group to `out`."""
    if not isinstance(agent, dict):
        return
    name = agent.get("name")
    if isinstance(name, str):
        out.add(name)
    account = agent.get("account")
    if isinstance(account, dict) and isinstance(account.get("name"), str):
        out.add(account["name"])
    for key in ("mbox", "mbox_sha1sum", "openid"):
        value = agent.get(key)
        if isinstance(value, str):
            out.add(value)
            if key == "mbox" and value.lower().startswith("mailto:"):
                out.add(value[len("mailto:"):])
    for member in agent.get("member", []) or []:
        _agent_sensitive_values(member, out)


def collect_sensitive_values(statements: list[dict]) -> set[str]:
    values: set[str] = set()
    for st in statements:
        _agent_sensitive_values(st.get("actor"), values)
        _agent_sensitive_values(st.get("authority"), values)
        context = st.get("context")
        if isinstance(context, dict):
            for key in REMOVED_CONTEXT_KEYS:
                _agent_sensitive_values(context.get(key), values)
    return {v.strip() for v in values if v and v.strip()}


# --- De-identification -------------------------------------------------------
def _actor_key(actor: dict) -> tuple:
    """Stable key for the actor's identifier (whichever IFI is present)."""
    for key in IFI_KEYS:
        value = actor.get(key)
        if key == "account" and isinstance(value, dict):
            return ("account", value.get("homePage"), value.get("name"))
        if isinstance(value, str):
            return (key, value)
    raise AnonymizationError("statement actor has no identifier")


def _pseudonym(batch_key: bytes, actor_key: tuple) -> str:
    message = json.dumps(actor_key, ensure_ascii=False).encode("utf-8")
    return hmac.new(batch_key, message, hashlib.sha256).hexdigest()


def deidentify(statements: list[dict]) -> list[dict]:
    batch_key = secrets.token_bytes(HASH_KEY_BYTES)  # lives only for this call
    codes: dict[tuple, str] = {}
    output = []
    for original in statements:
        st = json.loads(json.dumps(original))  # deep copy, input stays untouched
        actor = st.get("actor")
        if not isinstance(actor, dict):
            raise AnonymizationError("statement has no actor object")

        key = _actor_key(actor)
        if key not in codes:
            codes[key] = _pseudonym(batch_key, key)

        actor.pop("name", None)
        for ifi in IFI_KEYS:
            actor.pop(ifi, None)
        actor["account"] = {"homePage": ANON_HOMEPAGE, "name": codes[key]}

        context = st.get("context")
        if isinstance(context, dict):
            for ck in REMOVED_CONTEXT_KEYS:
                context.pop(ck, None)
        st.pop("authority", None)

        st["id"] = str(uuid.uuid4())
        output.append(st)
    return output


def find_leaks(output: list[dict], sensitive: set[str]) -> int:
    """Count original values that still appear anywhere in the output (keys or values)."""
    strings: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                strings.append(str(k))
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif node is not None:
            strings.append(str(node))

    walk(output)
    haystack = "\n".join(strings).casefold()
    return sum(1 for value in sensitive if value.casefold() in haystack)


# --- Pipeline ----------------------------------------------------------------
def output_file_name() -> str:
    """Date-based name, independent of the transfer_id (which may contain any characters)."""
    return f"anonymized_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:8]}.json"


def save_output(file_name: str, statements: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / file_name
    tmp = path.with_suffix(".json.tmp")
    # Same format as the input data: a bare list of statements, no wrapper.
    tmp.write_text(json.dumps(statements, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def forward(transfer_id: str, statements: list[dict]) -> None:
    next_url = os.environ.get("NEXT_URL", "").strip()
    if not next_url:
        log.info("transfer_id=%s forward=skipped reason=NEXT_URL_not_set", transfer_id)
        return
    try:
        with httpx.Client(timeout=FORWARD_TIMEOUT_S) as client:
            resp = client.post(next_url, json=statements)  # same bare list as the saved file
        resp.raise_for_status()
        log.info("transfer_id=%s forward=ok http_status=%s count=%d", transfer_id, resp.status_code, len(statements))
    except httpx.HTTPStatusError as exc:
        log.error("transfer_id=%s forward=failed http_status=%s", transfer_id, exc.response.status_code)
    except httpx.HTTPError as exc:
        log.error("transfer_id=%s forward=failed error=%s", transfer_id, type(exc).__name__)


def process(transfer_id: str, file_name: str, statements: list[dict]) -> None:
    """Runs after the 202 receipt has been sent (in FastAPI's threadpool).

    `transfer_id` must already be log-safe (see _log_safe).
    """
    try:
        output = deidentify(statements)
        leaks = find_leaks(output, collect_sensitive_values(statements))
        if leaks:
            log.error("transfer_id=%s status=blocked final_check_leaks=%d saved=0 forwarded=0", transfer_id, leaks)
            return
        save_output(file_name, output)
        students = len({st["actor"]["account"]["name"] for st in output})
        log.info("transfer_id=%s status=saved file=%s statements=%d students=%d",
                 transfer_id, file_name, len(output), students)
    except AnonymizationError as exc:
        log.error("transfer_id=%s status=failed reason=%s saved=0 forwarded=0", transfer_id, exc)
        return
    except Exception as exc:  # never let personal data reach the log via a traceback
        log.error("transfer_id=%s status=failed error=%s saved=0 forwarded=0", transfer_id, type(exc).__name__)
        return
    forward(transfer_id, output)


# --- API ---------------------------------------------------------------------
def _bad_request(reason: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"status": "rejected", "reason": reason})


def _parse_statements(raw: bytes) -> list[dict] | JSONResponse:
    """The body as a list of statement objects, or a 400 response."""
    try:
        body = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _bad_request("body is not valid JSON")
    if not isinstance(body, list):
        return _bad_request("body must be a JSON list of xAPI statements")
    for i, st in enumerate(body):
        if not isinstance(st, dict):
            return _bad_request(f"statements[{i}] is not a JSON object")
    return body


def _log_safe(value: str) -> str:
    """Escape control characters (newlines etc.) so an id cannot forge log lines."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def resolve_transfer_id(provided: str | None) -> tuple[str, bool]:
    """Return (transfer_id, generated).

    A caller-provided id is used as is and never rejected: any characters are
    fine, because it is not used in the file name. Without one, a placeholder
    id is generated with GENERATED_ID_PREFIX, so it is never mistaken for a
    real transfer id from the sender.
    """
    if provided is None or provided.strip() == "":
        return f"{GENERATED_ID_PREFIX}{uuid.uuid4()}", True
    return provided.strip(), False


# The body is validated by hand (to answer 400, not FastAPI's 422), so it is
# described here only so that /docs shows a request body editor.
STATEMENTS_REQUEST_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {"type": "array", "items": {"type": "object"}},
            "example": [
                {
                    "id": "6cb4d291-3827-5e2f-9e10-bcf5f434dacb",
                    "actor": {
                        "objectType": "Agent",
                        "name": "Example Student",
                        "account": {"homePage": "https://neptun.example.edu", "name": "ABC123"},
                    },
                    "verb": {"id": "http://adlnet.gov/expapi/verbs/failed", "display": {"en-US": "failed"}},
                    "object": {"objectType": "Activity", "id": "https://example.edu/xapi/course/lab/1"},
                }
            ],
        }
    },
}


@app.post(
    "/api/statements",
    status_code=202,
    openapi_extra={"requestBody": STATEMENTS_REQUEST_BODY},
    responses={400: {"description": "Body is not a JSON list of statement objects"}},
)
async def receive_statements(
    request: Request,
    background_tasks: BackgroundTasks,
    transfer_id: str | None = Query(
        default=None,
        description="Sender's transfer id. If omitted, a placeholder id starting with 'generated-' is created.",
    ),
):
    statements = _parse_statements(await request.body())
    if isinstance(statements, JSONResponse):
        return statements

    transfer_id, generated = resolve_transfer_id(transfer_id)
    file_name = output_file_name()
    log_id = _log_safe(transfer_id)
    log.info(
        "transfer_id=%s transfer_id_generated=%s status=accepted file=%s received=%d",
        log_id, str(generated).lower(), file_name, len(statements),
    )
    background_tasks.add_task(process, log_id, file_name, statements)
    return {
        "status": "accepted",
        "transfer_id": transfer_id,
        "output_file": file_name,
        "received": len(statements),
    }


def anonymize_now(statements: list[dict]) -> list[dict]:
    """De-identify and run the final check. Raises AnonymizationError on failure."""
    output = deidentify(statements)
    leaks = find_leaks(output, collect_sensitive_values(statements))
    if leaks:
        raise AnonymizationError(f"final check found {leaks} original value(s) in the output")
    return output


@app.post(
    "/api/anonymize",
    status_code=200,
    openapi_extra={"requestBody": STATEMENTS_REQUEST_BODY},
    responses={
        400: {"description": "Body is not a JSON list of statement objects"},
        422: {"description": "Statements could not be anonymized safely"},
    },
)
async def anonymize_statements(request: Request):
    """Anonymize the statements and return them in the response. Nothing is saved or forwarded."""
    statements = _parse_statements(await request.body())
    if isinstance(statements, JSONResponse):
        return statements
    try:
        output = await run_in_threadpool(anonymize_now, statements)
    except AnonymizationError as exc:
        log.error("endpoint=anonymize status=failed reason=%s received=%d", exc, len(statements))
        return JSONResponse(status_code=422, content={"status": "failed", "reason": str(exc)})
    except Exception as exc:  # never let personal data reach the log via a traceback
        log.error("endpoint=anonymize status=failed error=%s received=%d", type(exc).__name__, len(statements))
        return JSONResponse(status_code=500, content={"status": "failed", "reason": "internal error"})
    log.info("endpoint=anonymize status=returned statements=%d", len(output))
    return output


@app.get("/health")
async def health():
    return {"status": "ok"}
