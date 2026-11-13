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


def run(services: Services, data, headers=None, vla_id=VLA_ID, **settings) -> httpx.Response:
    configured = Settings(vla_id=vla_id, dva_url=DVA, **settings)

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


def statement(student: str, raw: int) -> dict:
    """An xAPI statement; the student is identified by actor.account.name."""
    return {
        "actor": {"objectType": "Agent", "account": {"homePage": "https://neptun.example.edu", "name": student}},
        "verb": {"id": "http://adlnet.gov/expapi/verbs/passed"},
        "result": {"score": {"raw": raw}},
    }


GRADES = [statement("s1", 4), statement("s2", 5)]


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


OTHER_VLA = "0b8d4c6e-5f1a-4e0f-9d2b-7a3c1e9f6b52"
CHAIN = {"data": GRADES, "contract": "https://contract.test/contracts/7", "params": {"foo": "bar"}}


def test_a_service_chain_envelope_is_unwrapped_and_only_its_data_is_attested():
    services = Services()

    response = run(services, CHAIN, forward_url=FORWARD)

    assert response.status_code == 200
    assert services.bodies(f"{DVA}/attestation")[0]["data"] == GRADES
    assert services.bodies(FORWARD) == [GRADES]


def test_the_vla_in_the_params_wins_over_the_configured_one():
    services = Services()

    response = run(services, {**CHAIN, "params": {"vlaID": OTHER_VLA}})

    assert response.status_code == 200
    assert services.bodies(f"{DVA}/attestation")[0]["vlaID"] == OTHER_VLA


def test_the_params_alone_name_the_vla_when_none_is_configured():
    services = Services()

    response = run(services, {**CHAIN, "params": {"vlaID": OTHER_VLA}}, vla_id=None)

    assert response.status_code == 200
    assert services.bodies(f"{DVA}/attestation")[0]["vlaID"] == OTHER_VLA


def test_without_params_the_configured_vla_is_used():
    services = Services()

    run(services, CHAIN)

    assert services.bodies(f"{DVA}/attestation")[0]["vlaID"] == VLA_ID


@pytest.mark.parametrize("body", [GRADES, CHAIN])
def test_no_vla_anywhere_is_rejected_before_any_service_is_called(body):
    services = Services()

    response = run(services, body, vla_id=None, anonymizer_url=ANONYMIZER)

    assert response.status_code == 422
    assert "VLA" in response.json()["detail"]
    assert services.calls == []


def test_a_vla_id_that_is_not_a_uuid_is_rejected():
    services = Services()

    response = run(services, {**CHAIN, "params": {"vlaID": "not-a-uuid"}})

    assert response.status_code == 422
    assert "not a valid UUID" in response.json()["detail"]
    assert services.calls == []


def test_the_contract_in_a_service_chain_envelope_identifies_the_contract_unless_the_header_does():
    services = Services()

    run(services, CHAIN)
    run(services, CHAIN, headers={"x-ptx-contractId": "https://contract.test/contracts/other"})

    from_body, from_header = [call["contractID"] for call in services.bodies(f"{DVA}/attestation")]
    assert from_body == as_uuid("https://contract.test/contracts/7")
    assert from_header == as_uuid("https://contract.test/contracts/other")


def test_an_object_that_merely_has_a_data_field_is_still_the_data_itself():
    services = Services()
    plain = {"data": [1, 2, 3], "note": "not an envelope"}

    run(services, plain)

    assert services.bodies(f"{DVA}/attestation")[0]["data"] == plain


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


def test_the_vla_is_optional_in_the_settings(monkeypatch):
    monkeypatch.delenv("VLA_ID", raising=False)

    assert Settings.from_env().vla_id is None


def test_the_settings_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("VLA_ID", VLA_ID)
    monkeypatch.setenv("DVA_URL", "http://dva:9090/")
    monkeypatch.setenv("ANONYMIZER_URL", ANONYMIZER)
    monkeypatch.delenv("FORWARD_URL", raising=False)

    settings = Settings.from_env()

    assert (settings.vla_id, settings.dva_url, settings.anonymizer_url, settings.forward_url) == (
        VLA_ID, "http://dva:9090", ANONYMIZER, None)
