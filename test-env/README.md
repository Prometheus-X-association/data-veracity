# DVA Test Environment

Just run all [karate](https://karatelabs.github.io/karate/) tests:
```console
$ docker compose --profile karate up --abort-on-container-exit
```

(Will start all necessary services using Docker Compose, run the test scenarios and then stop everything.)

---

Start a local test environment with a dummy callback server in the background:
```console
$ docker compose --profile dev up -d
```

---

Start only the core DVA services without any dummies or other helpers in the background:
```console
$ docker compose up -d
```
