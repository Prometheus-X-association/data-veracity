import json
import uuid
from collections import Counter

import httpx
import pytest
from fastapi.testclient import TestClient

from main import Settings, app, as_uuid, get_client, get_settings

ANONYMIZED_VLA = "02f0afb4-861e-44dd-8258-300ea76aba09"
AGGREGATED_VLA = "5b8c7d1e-3a94-4f6b-8e21-9c0d4a7f1e63"
OTHER_VLA = "0b8d4c6e-5f1a-4e0f-9d2b-7a3c1e9f6b52"

DVA = "http://dva.test:9090"
ANONYMIZER = "http://anonymizer.test/anonymize"
AGGREGATOR = "http://aggregator.test/aggregate"
ATTESTATION = f"{DVA}/attestation"

PASSING = {"evaluationPassing": True, "jws": "a.b.c", "evaluationResults": [{"engine": "JQ", "success": True}]}
FAILING = {"evaluationPassing": False, "evaluationResults": [{"engine": "JQ", "success": False, "details": "too few"}]}


def statement(student: str, raw: int = 3) -> dict:
    """An xAPI statement; the student is identified by actor.account.name."""
    return {
        "actor": {"objectType": "Agent", "name": "Real Name", "account": {"homePage": "https://neptun.example.edu", "name": student}},
        "verb": {"id": "http://adlnet.gov/expapi/verbs/passed"},
        "result": {"score": {"raw": raw}},
    }


STATEMENTS = [statement("a"), statement("a"), statement("b")]


class Services:
    """Stands in for the anonymizer, the DVA and the aggregator, and records the calls.

    The anonymizer marks every statement as anonymized, and the aggregator makes one row of
    `name` and `events` per student, so the tests can tell which data went where.
    """

    def __init__(self, attestations=None, dva_status=None, anonymizer_status=200, aggregator_status=200,
                 anonymizer_answer=None, aggregator_answer=None):
        # What the DVA answers per VLA, and with which status
        self.attestations = {ANONYMIZED_VLA: PASSING, AGGREGATED_VLA: PASSING, OTHER_VLA: PASSING, **(attestations or {})}
        self.dva_status = dva_status or {}
        self.anonymizer_status, self.aggregator_status = anonymizer_status, aggregator_status
        self.anonymizer_answer, self.aggregator_answer = anonymizer_answer, aggregator_answer
        self.calls: list[tuple[str, dict | list]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        url, body = str(request.url), json.loads(request.content)
        self.calls.append((url, body))
        if url == ANONYMIZER:
            answer = self.anonymizer_answer if self.anonymizer_answer is not None else [{**s, "anonymized": True} for s in body]
            return httpx.Response(self.anonymizer_status, json=answer)
        if url == AGGREGATOR:
            events = Counter(s["actor"]["account"]["name"] for s in body)
            answer = self.aggregator_answer if self.aggregator_answer is not None else [{"name": n, "events": c} for n, c in sorted(events.items())]
            return httpx.Response(self.aggregator_status, json=answer)
        if url == ATTESTATION:
            vla = body["vlaID"]
            return httpx.Response(self.dva_status.get(vla, 200), json=self.attestations[vla])
        raise AssertionError(f"unexpected call to {url}")

    def bodies(self, url: str) -> list:
        return [body for called, body in self.calls if called == url]

    def urls(self) -> list[str]:
        return [url for url, _ in self.calls]


def run(services: Services, body, headers=None, **settings) -> httpx.Response:
    configured = Settings(**{
        "anonymized_vla_id": ANONYMIZED_VLA, "aggregated_vla_id": AGGREGATED_VLA,
        "dva_url": DVA, "anonymizer_url": ANONYMIZER, "aggregator_url": AGGREGATOR, **settings})

    async def client():
        async with httpx.AsyncClient(transport=httpx.MockTransport(services.handler)) as c:
            yield c

    app.dependency_overrides[get_settings] = lambda: configured
    app.dependency_overrides[get_client] = client
    try:
        with TestClient(app) as test_client:
            return test_client.post("/analyse", json=body, headers=headers or {})
    finally:
        app.dependency_overrides.clear()


# --- The flow ------------------------------------------------------------------------------------

def test_the_data_is_anonymized_attested_aggregated_attested_again_and_returned():
    services = Services()

    response = run(services, STATEMENTS)

    assert response.status_code == 200
    assert services.urls() == [ANONYMIZER, ATTESTATION, AGGREGATOR, ATTESTATION]

    anonymized = [{**s, "anonymized": True} for s in STATEMENTS]
    aggregated = [{"name": "a", "events": 2}, {"name": "b", "events": 1}]
    assert services.bodies(ANONYMIZER) == [STATEMENTS]

    first, second = services.bodies(ATTESTATION)
    # The anonymized data is attested against its VLA, and only then aggregated
    assert (first["vlaID"], first["data"]) == (ANONYMIZED_VLA, anonymized)
    assert services.bodies(AGGREGATOR) == [anonymized]
    # The aggregated data is attested against the other VLA
    assert (second["vlaID"], second["data"]) == (AGGREGATED_VLA, aggregated)

    body = response.json()
    assert body["data"] == aggregated
    assert body["attestations"] == {
        "anonymized": {"vlaID": ANONYMIZED_VLA, "jws": "a.b.c", "evaluationResults": PASSING["evaluationResults"]},
        "aggregated": {"vlaID": AGGREGATED_VLA, "jws": "a.b.c", "evaluationResults": PASSING["evaluationResults"]},
    }
    assert first["exchangeID"] == second["exchangeID"] == body["exchangeID"]
    assert first["contractID"] == second["contractID"] == body["contractID"]
    uuid.UUID(body["exchangeID"])
    uuid.UUID(body["contractID"])


def test_a_service_chain_envelope_is_unwrapped_and_only_its_data_is_anonymized():
    services = Services()
    envelope = {"data": STATEMENTS, "contract": "https://contract.test/contracts/7", "params": {"foo": "bar"}}

    response = run(services, envelope)

    assert response.status_code == 200
    assert services.bodies(ANONYMIZER) == [STATEMENTS]


def test_an_object_that_merely_has_a_data_field_is_still_the_data_itself():
    services = Services()
    plain = {"data": [1, 2, 3], "note": "not an envelope"}

    # The mock anonymizer needs statements, so it is the anonymizer that sees the object
    services.anonymizer_answer = [statement("a")]
    run(services, plain)

    assert services.bodies(ANONYMIZER) == [plain]


# --- The VLAs ------------------------------------------------------------------------------------

def envelope(**params) -> dict:
    return {"data": STATEMENTS, "contract": "https://contract.test/contracts/7", "params": params}


def vlas_used(services: Services) -> tuple[str, str]:
    first, second = services.bodies(ATTESTATION)
    return first["vlaID"], second["vlaID"]


def test_the_vlas_named_in_the_params_win_over_the_configured_ones():
    other = "7e2a9c4b-1d83-4b5e-a6f0-3c8d9e1b2a47"
    services = Services(attestations={other: PASSING})

    response = run(services, envelope(anonymizedVlaID=OTHER_VLA, aggregatedVlaID=other))

    assert response.status_code == 200
    assert vlas_used(services) == (OTHER_VLA, other)


def test_each_vla_can_come_from_the_params_or_from_the_configuration_independently():
    services = Services()

    run(services, envelope(aggregatedVlaID=OTHER_VLA))
    assert vlas_used(services) == (ANONYMIZED_VLA, OTHER_VLA)

    services = Services()
    run(services, envelope(anonymizedVlaID=OTHER_VLA))
    assert vlas_used(services) == (OTHER_VLA, AGGREGATED_VLA)


def test_the_params_alone_can_name_both_vlas_when_none_is_configured():
    services = Services()

    response = run(services, envelope(anonymizedVlaID=ANONYMIZED_VLA, aggregatedVlaID=AGGREGATED_VLA),
                   anonymized_vla_id=None, aggregated_vla_id=None)

    assert response.status_code == 200
    assert vlas_used(services) == (ANONYMIZED_VLA, AGGREGATED_VLA)


@pytest.mark.parametrize("missing, settings, params", [
    ("anonymized", {"anonymized_vla_id": None}, {}),
    ("aggregated", {"aggregated_vla_id": None}, {}),
    ("anonymized", {"anonymized_vla_id": None, "aggregated_vla_id": None}, {"aggregatedVlaID": AGGREGATED_VLA}),
])
def test_a_missing_vla_is_rejected_before_any_service_is_called(missing, settings, params):
    services = Services()

    response = run(services, envelope(**params), **settings)

    assert response.status_code == 422
    assert f"no VLA for the {missing} data" in response.json()["detail"]
    assert services.calls == []


def test_a_vla_id_that_is_not_a_uuid_is_rejected_before_any_service_is_called():
    services = Services()

    response = run(services, envelope(aggregatedVlaID="not-a-uuid"))

    assert response.status_code == 422
    assert "not a valid UUID" in response.json()["detail"]
    assert services.calls == []


# --- Data that fails a VLA -----------------------------------------------------------------------

def test_anonymized_data_that_fails_its_vla_stops_the_flow_before_the_aggregation():
    services = Services(attestations={ANONYMIZED_VLA: FAILING})

    response = run(services, STATEMENTS)

    assert response.status_code == 422
    assert response.json() == {
        "stage": "attestation-anonymized",
        "detail": "the data does not satisfy the VLA",
        "evaluationResults": FAILING["evaluationResults"],
    }
    assert services.urls() == [ANONYMIZER, ATTESTATION]


def test_aggregated_data_that_fails_its_vla_is_not_returned():
    services = Services(attestations={AGGREGATED_VLA: FAILING})

    response = run(services, STATEMENTS)

    assert response.status_code == 422
    body = response.json()
    assert body["stage"] == "attestation-aggregated"
    assert body["evaluationResults"][0]["details"] == "too few"
    assert "data" not in body
    assert services.urls() == [ANONYMIZER, ATTESTATION, AGGREGATOR, ATTESTATION]


# --- Services that fail --------------------------------------------------------------------------

@pytest.mark.parametrize("failing, stage, calls", [
    ({"anonymizer_status": 500}, "anonymization", [ANONYMIZER]),
    ({"dva_status": {ANONYMIZED_VLA: 500}}, "attestation-anonymized", [ANONYMIZER, ATTESTATION]),
    ({"aggregator_status": 503}, "aggregation", [ANONYMIZER, ATTESTATION, AGGREGATOR]),
    ({"dva_status": {AGGREGATED_VLA: 500}}, "attestation-aggregated", [ANONYMIZER, ATTESTATION, AGGREGATOR, ATTESTATION]),
])
def test_a_failing_service_stops_the_flow_and_is_named(failing, stage, calls):
    services = Services(**failing)

    response = run(services, STATEMENTS)

    assert response.status_code == 502
    assert response.json()["stage"] == stage
    assert services.urls() == calls


@pytest.mark.parametrize("answer, stage", [
    ({"anonymizer_answer": {"not": "a list"}}, "anonymization"),
    ({"aggregator_answer": "nope"}, "aggregation"),
])
def test_an_answer_that_is_not_a_list_is_reported(answer, stage):
    services = Services(**answer)

    response = run(services, STATEMENTS)

    assert response.status_code == 502
    assert response.json()["stage"] == stage
    assert "did not answer with a list" in response.json()["detail"]


# --- The exchange and the contract ---------------------------------------------------------------

def test_the_pdc_identifiers_become_stable_uuids_in_both_attestations():
    services = Services()
    headers = {"x-ptx-dataExchangeId": "66e84e6fa000b970362d952e", "x-ptx-contractId": "https://contract.test/contracts/1"}

    run(services, STATEMENTS, headers=headers)

    for attested in services.bodies(ATTESTATION):
        assert attested["exchangeID"] == as_uuid("66e84e6fa000b970362d952e")
        assert attested["contractID"] == as_uuid("https://contract.test/contracts/1")
    assert as_uuid("66e84e6fa000b970362d952e") != as_uuid("https://contract.test/contracts/1")


def test_the_contract_in_a_service_chain_envelope_identifies_the_contract_unless_the_header_does():
    services = Services()
    body = envelope()

    run(services, body)
    run(services, body, headers={"x-ptx-contractId": "https://contract.test/contracts/other"})

    from_body, _, from_header, _ = [call["contractID"] for call in services.bodies(ATTESTATION)]
    assert from_body == as_uuid("https://contract.test/contracts/7")
    assert from_header == as_uuid("https://contract.test/contracts/other")


def test_an_identifier_that_already_is_a_uuid_is_kept():
    known = str(uuid.uuid4())

    assert as_uuid(known) == known
    assert as_uuid(known.upper()) == known


# --- Settings ------------------------------------------------------------------------------------

def test_the_settings_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("ANONYMIZED_VLA_ID", ANONYMIZED_VLA)
    monkeypatch.setenv("AGGREGATED_VLA_ID", AGGREGATED_VLA)
    monkeypatch.setenv("DVA_URL", "http://dva:9090/")
    monkeypatch.setenv("ANONYMIZER_URL", ANONYMIZER)
    monkeypatch.setenv("AGGREGATOR_URL", AGGREGATOR)

    settings = Settings.from_env()

    assert (settings.anonymized_vla_id, settings.aggregated_vla_id, settings.dva_url) == (
        ANONYMIZED_VLA, AGGREGATED_VLA, "http://dva:9090")
    assert (settings.anonymizer_url, settings.aggregator_url) == (ANONYMIZER, AGGREGATOR)


def test_everything_but_the_vlas_has_a_default(monkeypatch):
    for name in ("ANONYMIZED_VLA_ID", "AGGREGATED_VLA_ID", "DVA_URL", "ANONYMIZER_URL", "AGGREGATOR_URL", "TIMEOUT_SECONDS"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert (settings.anonymized_vla_id, settings.aggregated_vla_id) == (None, None)
    assert settings.anonymizer_url == "http://xapi-anonymizer:8001/api/anonymize"
    assert settings.aggregator_url == "http://xapi-aggregation:8002/api/aggregate"
