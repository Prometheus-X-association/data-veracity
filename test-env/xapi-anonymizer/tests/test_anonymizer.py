import copy
import json
import re
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import main

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "xapi_statements.json"
EXTRA = ROOT / "szoftech_pseudo_statements.json"  # larger extra dataset, if present


def load(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["statements"] if isinstance(data, dict) else data


def datasets():
    params = []
    for path in (SAMPLE, EXTRA):
        params.append(pytest.param(path, marks=pytest.mark.skipif(not path.exists(), reason=f"{path.name} missing")))
    return params


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.delenv("NEXT_URL", raising=False)
    return TestClient(main.app)


CODE_RE = re.compile(r"^[0-9a-f]{64}$")  # HMAC-SHA256 hex digest


def outputs(tmp_path) -> list[Path]:
    out = tmp_path / "output"
    return sorted(out.glob("anonymized_*.json")) if out.exists() else []


def strip_changed(st: dict) -> dict:
    """Everything the anonymizer is allowed to change, removed."""
    st = copy.deepcopy(st)
    st.pop("id", None)
    st.pop("actor", None)
    st.pop("authority", None)
    for k in ("instructor", "team"):
        st.get("context", {}).pop(k, None)
    return st


def original_values(statements: list[dict]) -> set[str]:
    values = set()
    for st in statements:
        a = st["actor"]
        values.add(a.get("name"))
        values.add((a.get("account") or {}).get("name"))
        values.add(a.get("mbox"))
        values.add(a.get("openid"))
    return {v for v in values if v}


def run_ok(client, tmp_path, statements):
    r = client.post("/api/statements", json=statements)
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "accepted"
    assert body["received"] == len(statements)
    files = outputs(tmp_path)
    assert [f.name for f in files] == [body["output_file"]]
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert isinstance(saved, list)  # bare list, like the input data
    return body, saved


# --- tests --------------------------------------------------------------------
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.skipif(not SAMPLE.exists(), reason="xapi_statements.json missing")
def test_sample_receipt_counts(client, tmp_path):
    body, out = run_ok(client, tmp_path, load(SAMPLE))
    assert body["received"] == 36
    assert len(out) == 36
    codes = {st["actor"]["account"]["name"] for st in out}
    assert len(codes) == 4
    assert all(CODE_RE.match(c) for c in codes)


@pytest.mark.parametrize("path", datasets())
def test_deidentification(client, tmp_path, path):
    statements = load(path)
    _, out = run_ok(client, tmp_path, statements)
    assert len(out) == len(statements)

    # codes: hash-like, one per distinct original identifier, consistent within the batch
    mapping = {}
    for src, dst in zip(statements, out):
        acc = dst["actor"]["account"]
        assert acc["homePage"] == "https://anonymizer.example.edu"
        assert "name" not in dst["actor"]
        assert not ({"mbox", "openid", "mbox_sha1sum"} & dst["actor"].keys())
        key = json.dumps({k: src["actor"].get(k) for k in ("account", "mbox", "openid")}, sort_keys=True)
        assert mapping.setdefault(key, acc["name"]) == acc["name"]
    assert all(CODE_RE.match(c) for c in mapping.values())
    assert len(set(mapping.values())) == len(mapping)  # distinct students -> distinct codes

    # ids: all new and unique
    old_ids = {st.get("id") for st in statements}
    new_ids = [st["id"] for st in out]
    assert len(set(new_ids)) == len(new_ids)
    assert not old_ids & set(new_ids)

    # every other field identical
    for src, dst in zip(statements, out):
        assert strip_changed(src) == strip_changed(dst)
        assert "authority" not in dst
        assert not ({"instructor", "team"} & dst.get("context", {}).keys())

    # no original names / Neptun codes anywhere
    text = json.dumps(out, ensure_ascii=False).casefold()
    for value in original_values(statements):
        assert value.casefold() not in text


def test_removes_instructor_team_authority(client, tmp_path):
    st = {
        "id": "11111111-1111-1111-1111-111111111111",
        "actor": {"objectType": "Agent", "name": "Kiss Anna", "mbox": "mailto:anna@example.edu"},
        "verb": {"id": "http://adlnet.gov/expapi/verbs/attempted"},
        "object": {"id": "https://example.edu/a"},
        "authority": {"name": "LRS Admin", "mbox": "mailto:admin@example.edu"},
        "context": {"instructor": {"name": "Dr. Tanár", "mbox": "mailto:t@example.edu"},
                    "team": {"objectType": "Group", "name": "Team 7"}, "platform": "Moodle"},
    }
    _, out = run_ok(client, tmp_path, [st, copy.deepcopy(st)])
    code = out[0]["actor"]["account"]["name"]
    assert CODE_RE.match(code)
    assert out[0]["actor"] == {"objectType": "Agent",
                               "account": {"homePage": "https://anonymizer.example.edu", "name": code}}
    assert out[1]["actor"]["account"]["name"] == code
    assert out[0]["context"] == {"platform": "Moodle"}
    assert "authority" not in out[0]


def leaked_batch():
    statements = load(SAMPLE if SAMPLE.exists() else EXTRA)[:36]
    statements[5]["context"].setdefault("extensions", {})["https://example.edu/xapi/ext/note"] = \
        f"submitted by {statements[0]['actor']['name']}"
    return statements


@pytest.mark.skipif(not (SAMPLE.exists() or EXTRA.exists()), reason="no dataset")
def test_final_check_blocks_leak(client, tmp_path, monkeypatch, caplog):
    forwarded = []
    monkeypatch.setenv("NEXT_URL", "http://127.0.0.1:9/should-not-be-called")
    monkeypatch.setattr(main, "forward", lambda *a: forwarded.append(a))
    statements = leaked_batch()
    with caplog.at_level("INFO", logger="anonymizer"):
        r = client.post("/api/statements", json=statements)
    assert r.status_code == 202
    tid = r.json()["transfer_id"]
    assert outputs(tmp_path) == []
    assert forwarded == []
    errors = [rec.getMessage() for rec in caplog.records if rec.levelname == "ERROR"]
    assert any(tid in m and "blocked" in m for m in errors)
    # logs never contain names or identifiers
    log_text = caplog.text.casefold()
    for value in original_values(statements):
        assert value.casefold() not in log_text


def test_bare_list_body(client, tmp_path):
    st = {"actor": {"name": "Kiss Anna", "account": {"homePage": "https://neptun.example.edu", "name": "ABC123"}},
          "verb": {"id": "v"}, "object": {"id": "o"}}
    r = client.post("/api/statements", json=[st, copy.deepcopy(st)])
    assert r.status_code == 202
    assert r.json()["received"] == 2
    files = outputs(tmp_path)
    assert len(files) == 1
    out = json.loads(files[0].read_text(encoding="utf-8"))
    codes = [s["actor"]["account"]["name"] for s in out]
    assert codes[0] == codes[1] and CODE_RE.match(codes[0])


def test_codes_differ_between_batches(client, tmp_path):
    client.post("/api/statements", json=[MINI_ST])
    client.post("/api/statements", json=[MINI_ST])
    codes = [json.loads(f.read_text(encoding="utf-8"))[0]["actor"]["account"]["name"] for f in outputs(tmp_path)]
    assert len(codes) == 2 and codes[0] != codes[1]


MINI_ST = {"actor": {"account": {"homePage": "https://neptun.example.edu", "name": "ABC123"}},
           "verb": {"id": "v"}, "object": {"id": "o"}}


FILE_NAME_RE = re.compile(r"^anonymized_\d{8}T\d{6}Z_[0-9a-f]{8}\.json$")


@pytest.mark.parametrize("tid", ["batch-2026_11", "../etc/passwd", "a/b c", "Übertragung #7", "x" * 500])
def test_provided_transfer_id_any_characters(client, tmp_path, tid):
    r = client.post("/api/statements", params={"transfer_id": tid}, json=[MINI_ST])
    assert r.status_code == 202
    body = r.json()
    assert body["transfer_id"] == tid
    assert "transfer_id_generated" not in body
    assert FILE_NAME_RE.match(body["output_file"])
    # the id never ends up in the path: exactly one file, directly in output/
    assert [f.name for f in outputs(tmp_path)] == [body["output_file"]]


def test_generated_transfer_id_is_marked(client, tmp_path):
    r = client.post("/api/statements", json=[MINI_ST])
    body = r.json()
    assert body["transfer_id"].startswith(main.GENERATED_ID_PREFIX)
    assert [f.name for f in outputs(tmp_path)] == [body["output_file"]]


def test_transfer_id_cannot_forge_log_lines(client, caplog):
    with caplog.at_level("INFO", logger="anonymizer"):
        client.post("/api/statements", params={"transfer_id": "x\nFAKE status=saved"}, json=[MINI_ST])
    assert not any(line.startswith("FAKE") for rec in caplog.records for line in rec.getMessage().splitlines())


@pytest.mark.parametrize("body", [
    b"not json",
    b'{\n [ {"id": "x"} ]\n}',
    b'"text"',
    b"42",
    b"{}",
    b'{"statements": [{"id": "x"}]}',  # wrapped form is not accepted
    b"[1, 2]",
])
def test_invalid_body(client, tmp_path, body):
    r = client.post("/api/statements", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json()["reason"]
    assert outputs(tmp_path) == []


# --- forwarding to a throwaway receiver -----------------------------------------
@pytest.fixture
def receiver():
    received = []
    app = FastAPI()

    @app.post("/in")
    async def inbox(request: Request):
        received.append(await request.json())
        return {"ok": True}

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/in", received
    server.should_exit = True
    thread.join(timeout=5)


@pytest.mark.skipif(not (SAMPLE.exists() or EXTRA.exists()), reason="no dataset")
def test_forwards_to_next_url(client, tmp_path, monkeypatch, receiver):
    url, received = receiver
    monkeypatch.setenv("NEXT_URL", url)
    statements = load(SAMPLE if SAMPLE.exists() else EXTRA)[:36]
    _, saved = run_ok(client, tmp_path, statements)
    assert len(received) == 1
    assert received[0] == saved  # exactly the saved output, bare list
    text = json.dumps(received[0], ensure_ascii=False)
    for value in original_values(statements):
        assert value not in text


def test_forward_failure_keeps_file(client, tmp_path, monkeypatch):
    monkeypatch.setenv("NEXT_URL", "http://127.0.0.1:9/nothing-listens-here")
    st = {"actor": {"mbox": "mailto:x@example.edu"}, "verb": {"id": "v"}, "object": {"id": "o"}}
    run_ok(client, tmp_path, [st])  # file saved despite the failed forward


# --- synchronous /api/anonymize ---------------------------------------------------
def test_anonymize_returns_data_and_saves_nothing(client, tmp_path, monkeypatch):
    forwarded = []
    monkeypatch.setattr(main, "forward", lambda *a: forwarded.append(a))
    st = {"id": "11111111-1111-1111-1111-111111111111",
          "actor": {"name": "Kiss Anna", "account": {"homePage": "https://neptun.example.edu", "name": "ABC123"}},
          "verb": {"id": "v"}, "object": {"id": "o"}}
    r = client.post("/api/anonymize", json=[st, copy.deepcopy(st)])
    assert r.status_code == 200
    out = r.json()
    assert isinstance(out, list) and len(out) == 2
    code = out[0]["actor"]["account"]["name"]
    assert CODE_RE.match(code) and out[1]["actor"]["account"]["name"] == code
    assert "name" not in out[0]["actor"]
    text = r.text.casefold()
    assert "kiss anna" not in text and "abc123" not in text
    assert outputs(tmp_path) == []
    assert forwarded == []


def test_anonymize_blocks_leak(client):
    st = {"actor": {"name": "Kiss Anna", "mbox": "mailto:anna@example.edu"},
          "verb": {"id": "v"}, "object": {"id": "o"},
          "context": {"extensions": {"note": "by Kiss Anna"}}}
    r = client.post("/api/anonymize", json=[st])
    assert r.status_code == 422
    assert "kiss anna" not in r.text.casefold()


def test_anonymize_missing_actor(client):
    r = client.post("/api/anonymize", json=[{"verb": {"id": "v"}, "object": {"id": "o"}}])
    assert r.status_code == 422


@pytest.mark.parametrize("body", [b"not json", b"{}", b"[1]"])
def test_anonymize_invalid_body(client, body):
    r = client.post("/api/anonymize", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 400
