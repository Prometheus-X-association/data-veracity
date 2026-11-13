import json
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

import main
from main import Settings, app, as_uuid, get_client, get_settings

VLA_ID = "02f0afb4-861e-44dd-8258-300ea76aba09"
DVA = "http://dva.test:9090"
ANONYMIZER = "http://anonymizer.test/anonymize"
FORWARD = "http://next.test/ingest"

PASSING = {"evaluationPassing": True, "jws": "a.b.c", "evaluationResults": [{"engine": "JQ", "success": True}]}
FAILING = {"evaluationPassing": False, "evaluationResults": [{"engine": "JQ", "success": False, "details": "too few"}]}


class Services:
    """Stands in for the anonymizer, the DVA and the next endpoint, and records the calls."""

    def __init__(self, attestation=PASSING, attestation_status=200, anonymizer_status=200, forward_status=200):
        self.attestation, self.attestation_status = attestation, attestation_status
        self.anonymizer_status, self.forward_status = anonymizer_status, forward_status
        self.calls: list[tuple[str, dict | list]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        url, body = str(request.url), json.loads(request.content)
        self.calls.append((url, body))
        if url == ANONYMIZER:
            return httpx.Response(self.anonymizer_status, json={"anonymized": body})
        if url == f"{DVA}/attestation":
            return httpx.Response(self.attestation_status, json=self.attestation)
        if url == FORWARD:
            return httpx.Response(self.forward_status, json={})
        raise AssertionError(f"unexpected call to {url}")

    def bodies(self, url: str) -> list:
        return [body for called, body in self.calls if called == url]


def run(services: Services, data, headers=None, **settings) -> httpx.Response:
    configured = Settings(vla_id=VLA_ID, dva_url=DVA, **settings)

    async def client():
        async with httpx.AsyncClient(transport=httpx.MockTransport(services.handler)) as c:
            yield c

    app.dependency_overrides[get_settings] = lambda: configured
    app.dependency_overrides[get_client] = client
    try:
        with TestClient(app) as test_client:
            return test_client.post("/analyse", json=data, headers=headers or {})
    finally:
        app.dependency_overrides.clear()


GRADES = [{"studentId": "s1", "grade": 4}, {"studentId": "s2", "grade": 5}]


def test_anonymizes_then_attests_the_anonymized_data_against_the_configured_vla_then_forwards_it():
    services = Services()

    response = run(services, GRADES, anonymizer_url=ANONYMIZER, forward_url=FORWARD)

    assert response.status_code == 200
    body = response.json()
    assert body["anonymization"] == "applied"
    assert body["forwarded"] is True
    assert body["attestation"]["jws"] == "a.b.c"
    assert body["attestation"]["vlaID"] == VLA_ID

    assert [url for url, _ in services.calls] == [ANONYMIZER, f"{DVA}/attestation", FORWARD]
    anonymized = {"anonymized": GRADES}
    assert services.bodies(ANONYMIZER) == [GRADES]
    (attested,) = services.bodies(f"{DVA}/attestation")
    assert attested["data"] == anonymized
    assert attested["vlaID"] == VLA_ID
    uuid.UUID(attested["exchangeID"])
    uuid.UUID(attested["contractID"])
    assert services.bodies(FORWARD) == [anonymized]


def test_without_an_anonymizer_the_mock_is_used_so_the_data_is_attested_as_it_is_and_the_response_says_so():
    services = Services()

    response = run(services, GRADES, forward_url=FORWARD)

    assert response.json()["anonymization"] == "mock"
    assert services.bodies(f"{DVA}/attestation")[0]["data"] == GRADES
    assert services.bodies(FORWARD) == [GRADES]


def test_data_that_fails_the_vla_is_not_forwarded_and_the_failed_checks_are_returned():
    services = Services(attestation=FAILING)

    response = run(services, GRADES, anonymizer_url=ANONYMIZER, forward_url=FORWARD)

    assert response.status_code == 422
    assert response.json()["evaluationResults"][0]["details"] == "too few"
    assert services.bodies(FORWARD) == []


def test_without_a_forward_endpoint_the_attested_data_is_reported_as_not_forwarded():
    services = Services()

    response = run(services, GRADES)

    assert response.status_code == 200
    assert response.json()["forwarded"] is False


def test_a_failing_anonymizer_stops_the_flow_before_the_dva():
    services = Services(anonymizer_status=500)

    response = run(services, GRADES, anonymizer_url=ANONYMIZER, forward_url=FORWARD)

    assert response.status_code == 502
    assert response.json()["stage"] == "anonymization"
    assert services.bodies(f"{DVA}/attestation") == []


def test_a_failing_dva_stops_the_flow_before_the_forward():
    services = Services(attestation_status=500)

    response = run(services, GRADES, forward_url=FORWARD)

    assert response.status_code == 502
    assert response.json()["stage"] == "attestation"
    assert services.bodies(FORWARD) == []


def test_a_failing_forward_is_reported():
    services = Services(forward_status=503)

    response = run(services, GRADES, forward_url=FORWARD)

    assert response.status_code == 502
    assert response.json()["stage"] == "forward"


def test_the_pdc_identifiers_become_stable_uuids():
    services = Services()
    headers = {"x-ptx-dataExchangeId": "66e84e6fa000b970362d952e", "x-ptx-contractId": "https://contract.test/contracts/1"}

    run(services, GRADES, headers=headers)
    run(services, GRADES, headers=headers)

    first, second = services.bodies(f"{DVA}/attestation")
    assert first["exchangeID"] == second["exchangeID"] == as_uuid("66e84e6fa000b970362d952e")
    assert first["contractID"] == as_uuid("https://contract.test/contracts/1")
    assert first["exchangeID"] != first["contractID"]


def test_an_identifier_that_already_is_a_uuid_is_kept():
    known = str(uuid.uuid4())

    assert as_uuid(known) == known
    assert as_uuid(known.upper()) == known


def test_the_service_does_not_start_without_a_vla(monkeypatch):
    monkeypatch.delenv("VLA_ID", raising=False)

    with pytest.raises(RuntimeError, match="VLA_ID"):
        Settings.from_env()


def test_the_settings_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("VLA_ID", VLA_ID)
    monkeypatch.setenv("DVA_URL", "http://dva:9090/")
    monkeypatch.setenv("ANONYMIZER_URL", ANONYMIZER)
    monkeypatch.delenv("FORWARD_URL", raising=False)

    settings = Settings.from_env()

    assert (settings.vla_id, settings.dva_url, settings.anonymizer_url, settings.forward_url) == (
        VLA_ID, "http://dva:9090", ANONYMIZER, None)
