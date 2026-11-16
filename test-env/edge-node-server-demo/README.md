# Edge node server demo

Orchestrates the edge node demo. The Dataspace Connector (PDC) POSTs xAPI statements to
`POST /analyse`, and this service

1. sends them to the **anonymizer** (`xapi-anonymizer`),
2. has the **DVA attest** the anonymized statements against a VLA,
3. sends the attested, anonymized statements to the **aggregator** (`xapi-aggregation`),
4. has the **DVA attest** the aggregated data against a second VLA,
5. sends the **aggregated data back**, together with the two attestations (AoVs).

If either attestation fails, the flow stops there: the aggregator is not called after a
failed first attestation, and nothing but the reason is returned after a failed second one.

## Run

With the test environment (`test-env/`), the `demo` profile starts this service and the two
it uses; the anonymizer and the aggregator are copies of the services in `../xapi-anonymizer`
and `../xapi-aggregation` (see their `SOURCE.md`):

```console
docker compose --profile demo up -d --build
```

| Service | In the network | On the host |
|---|---|---|
| this service | `edge-node-server-demo:8090` | `localhost:8090` |
| anonymizer | `xapi-anonymizer:8001` | `localhost:8101` |
| aggregator | `xapi-aggregation:8002` | `localhost:8102` |

Without Docker (against a running test environment):

```console
uv sync
DVA_URL=http://localhost:9091 ANONYMIZER_URL=http://localhost:8101/api/anonymize \
  AGGREGATOR_URL=http://localhost:8102/api/aggregate uv run uvicorn main:app --port 8090
```

Tests: `uv run pytest`.

## The VLAs

Two VLAs are needed, because the two data sets have different structure: the anonymized
statements identify the student by `actor.account.name`, the aggregated rows by `name`. A
VLA that checks one cannot check the other. Both can be built from the same "Minimum unique
values" template (`../test-data/vla-template/min-unique-values.json`), with
`field: actor.account.name` and `field: name`.

Each request names them in its `params`, or else the configured ones are used:

| `params`            | Configuration (environment) | The VLA for                |
|---------------------|-----------------------------|----------------------------|
| `anonymizedVlaID`   | `ANONYMIZED_VLA_ID`         | the anonymized statements  |
| `aggregatedVlaID`   | `AGGREGATED_VLA_ID`         | the aggregated data        |

`params` wins over the configuration, and each VLA is chosen independently. A request
without a usable ID for either VLA is rejected (`422`) before any service is called, and so
is an ID that is not a UUID.

## Configuration

| Variable            | Default                                        | Meaning                                  |
|---------------------|------------------------------------------------|------------------------------------------|
| `ANONYMIZED_VLA_ID` | *(unset)*                                      | See above.                               |
| `AGGREGATED_VLA_ID` | *(unset)*                                      | See above.                               |
| `DVA_URL`           | `http://dva-api-provider:9090`                 | DVA API base URL.                        |
| `ANONYMIZER_URL`    | `http://xapi-anonymizer:8001/api/anonymize`    | The synchronous anonymization endpoint.  |
| `AGGREGATOR_URL`    | `http://xapi-aggregation:8002/api/aggregate`   | The synchronous aggregation endpoint.    |
| `TIMEOUT_SECONDS`   | `30`                                           | Timeout of each call to another service. |

A request makes up to four calls, one after the other, so it can take several times
`TIMEOUT_SECONDS` if the services are slow. The caller (the PDC) waits for all of it.

## `POST /analyse`

The body is either the statements themselves (a JSON list), or, in a service chain, the
envelope the PDC wraps them in:

```json
{
  "data": [ ... ],
  "contract": "https://contract.example/contracts/1",
  "params": { "anonymizedVlaID": "<vla id>", "aggregatedVlaID": "<vla id>" }
}
```

A body is an envelope if it is an object with `data` and `params` and/or `contract`; anything
else is taken as the data. Only `data` is processed. `params` is what the service's entry in
the chain definition carries, so the VLAs can be chosen there.

The PDC's `x-ptx-dataExchangeId` and `x-ptx-contractId` headers identify the exchange and the
contract in the attestations; without the contract header, the envelope's `contract` does.
The DVA wants UUIDs, so an identifier that is not one is mapped to a stable UUID derived from
it (the same PDC identifier always gives the same UUID).

### Responses

`200`: the flow went through.

```json
{
  "data": [ { "name": "<pseudonym>", "events": 6, "result": "no result", "grade": "no grade" } ],
  "attestations": {
    "anonymized": { "vlaID": "...", "jws": "...", "evaluationResults": [ ... ] },
    "aggregated": { "vlaID": "...", "jws": "...", "evaluationResults": [ ... ] }
  },
  "exchangeID": "...",
  "contractID": "..."
}
```

`data` is the aggregated data. The AoVs (`jws`) are the DVA's credentials: the first attests
the anonymized statements, the second the aggregated data.

| Status | Meaning |
|--------|---------|
| `422`  | A VLA is missing or not a UUID (`detail` says which), or the data does not satisfy its VLA: `stage` is `attestation-anonymized` or `attestation-aggregated`, and `evaluationResults` says which checks failed. |
| `502`  | A service failed: `stage` is `anonymization`, `attestation-anonymized`, `aggregation` or `attestation-aggregated`, and `detail` says what it answered. |

## Example

A service chain request with the VLAs named in `params`, and the exchange and contract
identified in the headers. The data are xAPI statements, and the student is identified by
`actor.account.name`:

```console
curl -s -X POST http://localhost:8090/analyse \
  -H 'x-ptx-dataExchangeId: 3f9b6c1e-7a42-4d58-9c0e-2b1a8d5e6f47' \
  -H 'x-ptx-contractId: c7d2a9b4-18e3-4f6a-b05d-91e4c3a7f208' \
  -H 'Content-Type: application/json' \
  -d '{
    "params": { "anonymizedVlaID": "<vla id>", "aggregatedVlaID": "<vla id>" },
    "data": [
      {"actor": {"objectType": "Agent", "name": "Jane Doe", "account": {"homePage": "https://neptun.example.edu", "name": "AB12CD"}},
       "verb": {"id": "http://adlnet.gov/expapi/verbs/passed", "display": {"en-US": "passed"}},
       "object": {"id": "https://example.edu/xapi/course/software-engineering", "definition": {"type": "http://adlnet.gov/expapi/activities/course"}},
       "result": {"score": {"raw": 4}}},
      {"actor": {"objectType": "Agent", "name": "John Roe", "account": {"homePage": "https://neptun.example.edu", "name": "EF34GH"}},
       "verb": {"id": "http://adlnet.gov/expapi/verbs/failed", "display": {"en-US": "failed"}},
       "object": {"id": "https://example.edu/xapi/course/software-engineering", "definition": {"type": "http://adlnet.gov/expapi/activities/course"}},
       "result": {"score": {"raw": 1}}}
    ]
  }'
```

This has two students, so VLAs that require more than two distinct students fail it. A
realistic sample is `test_data_input_statements.json` (22 statements, 4 students).
