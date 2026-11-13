# Edge node server demo

Orchestrates the edge node demo. The Dataspace Connector (PDC) POSTs the data to
analyse to `POST /analyse`, and this service

1. **anonymizes** the data (the anonymization service is provided separately; until
   `ANONYMIZER_URL` is set, a mock leaves the data as it is),
2. has the **DVA attest** the anonymized data against one fixed VLA (`VLA_ID`),
3. **forwards** the anonymized data to `FORWARD_URL` if the attestation succeeded.

## Run

```console
uv sync
VLA_ID=<vla id> DVA_URL=http://localhost:9091 FORWARD_URL=<next endpoint> \
  uv run uvicorn main:app --port 8090
```

Tests: `uv run pytest`.

## Configuration

| Variable          | Default                       | Meaning                                                                      |
|-------------------|-------------------------------|------------------------------------------------------------------------------|
| `VLA_ID`          | *(required)*                  | VLA every request is attested against. The service does not start without it. |
| `DVA_URL`         | `http://dva-api-provider:9090`| DVA API base URL (from the host, the test environment's is `localhost:9091`). |
| `ANONYMIZER_URL`  | *(unset: mock)*               | Anonymization service. Unset: the mock is used and the data is **not** anonymized. |
| `FORWARD_URL`     | *(unset: not forwarded)*      | Where attested data is sent.                                                 |
| `TIMEOUT_SECONDS` | `30`                          | Timeout of each call to another service.                                     |

## `POST /analyse`

The body is the data, any JSON. The PDC's `x-ptx-dataExchangeId` and
`x-ptx-contractId` headers, when present, identify the exchange and contract in the
attestation. The DVA wants UUIDs, so an identifier that is not one is mapped to a
stable UUID derived from it (the same PDC identifier always gives the same UUID).

| Status | Meaning |
|--------|---------|
| `200`  | Attested. Body: `anonymization` (`applied` or `mock`), `attestation` (`jws`, `evaluationResults`, the IDs used) and `forwarded` (whether `FORWARD_URL` is set and was called). |
| `422`  | The data does not satisfy the VLA. Nothing was forwarded; `evaluationResults` says which checks failed. |
| `502`  | The anonymizer, the DVA or the forward endpoint failed. `stage` is `anonymization`, `attestation` or `forward`. |

## To be confirmed

* **Anonymization service contract.** Assumed: the data is POSTed as the JSON body and
  the anonymized data is the JSON body of the answer (`anonymize` in `main.py`).
* **What is forwarded.** The anonymized data only; the AoV (`jws`) is returned to the
  caller but not sent on.
