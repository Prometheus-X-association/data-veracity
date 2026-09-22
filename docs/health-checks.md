# Health checks

Every DVA service answers two endpoints:

* `GET /livez` – is the process up?  Always `pass`; checks nothing.  The
  container healthchecks (`HEALTHCHECK` in each Dockerfile) call it.
* `GET /readyz` – can the service do its work?  Checks the service's own
  dependencies, each with a 2 s timeout.

Both answer `application/health+json` with the `status` and `output` fields of
the IETF draft [health check response format][draft]:

```json
{"status": "pass"}
{"status": "warn", "output": "VLA_MANAGER_DB_URL is not set; data is kept in memory"}
{"status": "fail", "output": "postgres: connection refused"}
```

`status` is `pass`, `warn` (works, but degraded) or `fail`; `output` says why,
and is absent on `pass`.  `fail` answers `503`, the others `200`.  The schema
is `Health` in [`spec/components.yaml`](spec/components.yaml).

## What `/readyz` checks

| Service | `fail` when | `warn` when |
|---|---|---|
| `dva-api` | its Postgres, or the `/livez` of the VLA Manager API, processing or the VC Manager, does not answer | – |
| `dva-processing` | – (stateless, needs nothing) | – |
| `dva-vc-manager` | Postgres does not answer | `DVA_VC_MANAGER_DB_URL` is not set |
| `vla-manager-api` | Postgres does not answer | `VLA_MANAGER_DB_URL` is not set |
| `dva-dashboard`, `vla-manager` (nginx) | – | – |

Services call each other's `/livez`, never `/readyz`, so checks never cascade.

## Dashboard

The dashboard only reaches the gateway, so the gateway also serves
`GET /info/health`: its own `/readyz` answer and that of every service it
calls, keyed by service.  A service that does not answer with one within
2 s is reported as `fail`.

```console
$ curl -s localhost:9091/info/health
{"gateway":{"status":"pass"},"vla-manager":{"status":"pass"},"processing":{"status":"pass"},"vc-manager":{"status":"fail","output":"postgres: timed out"}}
```

[draft]: https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check-06
