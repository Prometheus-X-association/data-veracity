# Edge node server demo

Orchestrates the edge node demo. The Dataspace Connector (PDC) POSTs the data to
analyse to `POST /analyse`, and this service

1. **anonymizes** the data (the anonymization service is provided separately; until
   `ANONYMIZER_URL` is set, a mock leaves the data as it is),
2. has the **DVA attest** the anonymized data against a VLA (`params.vlaID` of the request,
   or else the configured `VLA_ID`),
3. **forwards** the anonymized data to `FORWARD_URL` if the attestation succeeded.

## Run

```console
uv sync
VLA_ID=<vla id, optional> DVA_URL=http://localhost:9091 FORWARD_URL=<next endpoint> \
  uv run uvicorn main:app --port 8090
```

Tests: `uv run pytest`.

## Configuration

| Variable          | Default                       | Meaning                                                                      |
|-------------------|-------------------------------|------------------------------------------------------------------------------|
| `VLA_ID`          | *(unset)*                     | VLA to attest against when the request does not name one in `params.vlaID`. Without it, every request has to. |
| `DVA_URL`         | `http://dva-api-provider:9090`| DVA API base URL (from the host, the test environment's is `localhost:9091`). |
| `ANONYMIZER_URL`  | *(unset: mock)*               | Anonymization service. Unset: the mock is used and the data is **not** anonymized. |
| `FORWARD_URL`     | *(unset: not forwarded)*      | Where attested data is sent.                                                 |
| `TIMEOUT_SECONDS` | `30`                          | Timeout of each call to another service.                                     |

## `POST /analyse`

The body is either the data itself (any JSON), or, in a service chain, the envelope the PDC
wraps it in:

```json
{ "data": [ ... ], "contract": "https://contract.example/contracts/1", "params": { "vlaID": "<vla id>" } }
```

A body is an envelope if it is an object with `data` and `params` and/or `contract`; anything
else is taken as the data. Only `data` is anonymized, attested and forwarded. `params` is what
the service's entry in the chain definition carries, so the VLA can be chosen there.

**Which VLA:** `params.vlaID` if the request has one, otherwise `VLA_ID`. With neither, the
request is rejected (`422`) before any service is called, and so is a `vlaID` that is not a UUID.

The PDC's `x-ptx-dataExchangeId` and
`x-ptx-contractId` headers, when present, identify the exchange and contract in the
attestation; without the contract header, the envelope's `contract` does. The DVA wants UUIDs, so an identifier that is not one is mapped to a
stable UUID derived from it (the same PDC identifier always gives the same UUID).

| Status | Meaning |
|--------|---------|
| `200`  | Attested. Body: `anonymization` (`applied` or `mock`), `attestation` (`jws`, `evaluationResults`, the IDs used) and `forwarded` (whether `FORWARD_URL` is set and was called). |
| `422`  | The data does not satisfy the VLA (nothing was forwarded; `evaluationResults` says which checks failed), or no usable VLA ID was given. |
| `502`  | The anonymizer, the DVA or the forward endpoint failed. `stage` is `anonymization`, `attestation` or `forward`. |

## Example

A service chain request, with the VLA named in `params` and the exchange and contract identified in the
headers. The list has 25 distinct students, so a VLA that requires at least 25 passes it:

```console
curl -s -X POST http://localhost:8090/analyse \
  -H 'x-ptx-dataExchangeId: 3f9b6c1e-7a42-4d58-9c0e-2b1a8d5e6f47' \
  -H 'x-ptx-contractId: c7d2a9b4-18e3-4f6a-b05d-91e4c3a7f208' \
  -H 'Content-Type: application/json' \
  -d '{
    "params": { "vlaID": "<vla id>" },
    "data": [
        {"studentId": "s0", "course": "math", "grade": 3},
        {"studentId": "s1", "course": "math", "grade": 3},
        {"studentId": "s2", "course": "math", "grade": 3},
        {"studentId": "s3", "course": "math", "grade": 3},
        {"studentId": "s4", "course": "math", "grade": 3},
        {"studentId": "s5", "course": "math", "grade": 3},
        {"studentId": "s6", "course": "math", "grade": 3},
        {"studentId": "s7", "course": "math", "grade": 3},
        {"studentId": "s8", "course": "math", "grade": 3},
        {"studentId": "s9", "course": "math", "grade": 3},
        {"studentId": "s10", "course": "math", "grade": 3},
        {"studentId": "s11", "course": "math", "grade": 3},
        {"studentId": "s12", "course": "math", "grade": 3},
        {"studentId": "s13", "course": "math", "grade": 3},
        {"studentId": "s14", "course": "math", "grade": 3},
        {"studentId": "s15", "course": "math", "grade": 3},
        {"studentId": "s16", "course": "math", "grade": 3},
        {"studentId": "s17", "course": "math", "grade": 3},
        {"studentId": "s18", "course": "math", "grade": 3},
        {"studentId": "s19", "course": "math", "grade": 3},
        {"studentId": "s20", "course": "math", "grade": 3},
        {"studentId": "s21", "course": "math", "grade": 3},
        {"studentId": "s22", "course": "math", "grade": 3},
        {"studentId": "s23", "course": "math", "grade": 3},
        {"studentId": "s24", "course": "math", "grade": 3}
    ]
  }'
```

Without `params`, send the list itself as the body, and the VLA is the configured `VLA_ID`.

## To be confirmed

* **Anonymization service contract.** Assumed: the data is POSTed as the JSON body and
  the anonymized data is the JSON body of the answer (`anonymize` in `main.py`).
* **What is forwarded.** The anonymized data only; the AoV (`jws`) is returned to the
  caller but not sent on.
