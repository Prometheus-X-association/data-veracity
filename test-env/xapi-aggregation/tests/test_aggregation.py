import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main

TEST_INPUT = Path(__file__).resolve().parent.parent / "test_input.json"
COURSE = "http://adlnet.gov/expapi/activities/course"
LAB = "http://adlnet.gov/expapi/activities/assessment"


def st(student, verb="completed", type_=LAB, raw=None):
    s = {
        "actor": {"objectType": "Agent", "account": {"homePage": "https://anonymizer.example.edu", "name": student}},
        "verb": {"id": f"http://adlnet.gov/expapi/verbs/{verb}", "display": {"en-US": verb}},
        "object": {"objectType": "Activity", "id": "https://example.edu/x", "definition": {"type": type_}},
    }
    if raw is not None:
        s["result"] = {"score": {"raw": raw}}
    return s


# 4 students, unsorted on purpose: failed/1, passed/3, passed/3, no result/no grade
SMALL = (
    [st("student-002", "passed", LAB, 4), st("student-002", "passed", COURSE, 3)]
    + [st("student-001", "failed", LAB, 1)] * 3 + [st("student-001", "failed", COURSE, 1)]
    + [st("student-004")] * 2
    + [st("student-003", "passed", COURSE, 3)]
    + [{"actor": {"objectType": "Agent"}, "verb": {}, "object": {}}]  # no account.name -> skipped
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.delenv("NEXT_URL", raising=False)
    return TestClient(main.app)


def saved(tmp_path):
    files = list((tmp_path / "output").glob("aggregated_*.json"))
    assert len(files) == 1
    return files[0], json.loads(files[0].read_text())


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_small_batch_results(client, tmp_path):
    r = client.post("/api/statements?transfer_id=t-1", json=SMALL)
    assert r.status_code == 202
    assert r.json() == {"status": "accepted", "transfer_id": "t-1", "received": len(SMALL)}
    path, rows = saved(tmp_path)
    assert re.fullmatch(r"aggregated_\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d_[0-9a-f]{8}\.json", path.name)
    assert [x["name"] for x in rows] == ["student-001", "student-002", "student-003", "student-004"]
    assert [x["result"] for x in rows] == ["failed", "passed", "passed", "no result"]
    assert [x["grade"] for x in rows] == [1, 3, 3, "no grade"]
    assert [x["events"] for x in rows] == [4, 2, 1, 2]


def test_generated_transfer_id(client, tmp_path):
    r = client.post("/api/statements", json=SMALL)
    assert r.json()["transfer_id"].startswith("generated-")
    saved(tmp_path)


def test_transfer_id_not_in_file_name(client, tmp_path):
    r = client.post("/api/statements", params={"transfer_id": "../../evil/x\ny"}, json=SMALL)
    assert r.json()["transfer_id"] == "../../evil/x\ny"
    path, _ = saved(tmp_path)
    assert path.parent == tmp_path / "output" and "evil" not in path.name


@pytest.mark.parametrize("body", ['{"a": 1}', "not json", '"text"', "[1, 2]"])
def test_not_a_json_array_is_400(client, tmp_path, body):
    r = client.post("/api/statements", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json()["status"] == "rejected" and r.json()["reason"]
    assert not (tmp_path / "output").exists()


def test_aggregate_returns_rows_directly(client, tmp_path):
    r = client.post("/api/aggregate", json=SMALL)
    assert r.status_code == 200
    assert r.json() == [
        {"name": "student-001", "events": 4, "result": "failed", "grade": 1},
        {"name": "student-002", "events": 2, "result": "passed", "grade": 3},
        {"name": "student-003", "events": 1, "result": "passed", "grade": 3},
        {"name": "student-004", "events": 2, "result": "no result", "grade": "no grade"},
    ]
    assert not (tmp_path / "output").exists()  # nothing saved


@pytest.mark.parametrize("body", ['{"a": 1}', "not json", "[1, 2]"])
def test_aggregate_bad_body_is_400(client, body):
    r = client.post("/api/aggregate", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 400 and r.json()["status"] == "rejected"


@pytest.mark.skipif(not TEST_INPUT.exists(), reason="test_input.json missing")
def test_full_test_input(client, tmp_path):
    data = json.loads(TEST_INPUT.read_text())
    r = client.post("/api/statements?transfer_id=full", content=TEST_INPUT.read_bytes(),
                    headers={"content-type": "application/json"})
    assert r.status_code == 202 and r.json()["received"] == len(data)
    _, rows = saved(tmp_path)

    # independent expectation
    events, finals = {}, {}
    for s in data:
        n = s["actor"]["account"]["name"]
        events[n] = events.get(n, 0) + 1
        if s["object"].get("definition", {}).get("type") == COURSE:
            finals[n] = (s["verb"]["display"]["en-US"], s["result"]["score"]["raw"])
    expected = [{"name": n, "events": events[n],
                 "result": finals.get(n, ("no result", "no grade"))[0],
                 "grade": finals.get(n, ("no result", "no grade"))[1]} for n in sorted(events)]
    assert rows == expected
    assert sum(x["events"] for x in rows) == len(data)
    assert {x["result"] for x in rows} == {"passed", "failed", "no result"}


def test_forward_to_receiver(client, tmp_path, monkeypatch):
    received = []

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Receiver)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("NEXT_URL", f"http://127.0.0.1:{server.server_port}/in")
        assert client.post("/api/statements?transfer_id=fw", json=SMALL).status_code == 202
    finally:
        server.shutdown()
    _, rows = saved(tmp_path)
    assert received == [rows]
    assert isinstance(received[0], list) and len(received[0]) == 4


def test_forward_failure_keeps_file(client, tmp_path, monkeypatch):
    monkeypatch.setenv("NEXT_URL", "http://127.0.0.1:9/unreachable")
    assert client.post("/api/statements", json=SMALL).status_code == 202
    _, rows = saved(tmp_path)
    assert len(rows) == 4
