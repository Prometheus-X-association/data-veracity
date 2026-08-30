# DVA Test Environment

From this directory, start the complete local environment:
```console
docker compose up -d --build
```

Wait until every service reports healthy:
```console
docker compose ps
```

## Interfaces

| Interface | Address |
|---|---|
| Provider dashboard | http://localhost:3011 |
| Consumer dashboard | http://localhost:3012 |
| VLA Manager | http://localhost:3020 |
| Provider DVA API | http://localhost:9091/swagger |
| Consumer DVA API | http://localhost:9092/swagger |
| VLA Manager DVA API | http://localhost:9099/swagger |
| VLA Manager API | http://localhost:8000/swagger |
| VC Manager API | http://localhost:8001/swagger |

Each frontend talks to exactly one backend: the dashboards to their own DVA API,
the VLA Manager to the DVA API dedicated to it. The DVA APIs reach the VLA
Manager API, the VC Manager and DVA Processing on their behalf, so the VLA
Manager API and VC Manager are exposed here for inspection rather than for the
frontends to call.

The environment follows the refactored HTTP-only architecture. It does not start
RabbitMQ.

To inspect a service while reviewing a failure:
```console
docker compose logs --follow <service-name>
```

To stop the environment without deleting database volumes:
```console
docker compose down
```


## Testing

Just run all [karate](https://karatelabs.github.io/karate/) tests:
```console
docker compose --profile karate up --abort-on-container-exit
```

(Will start all necessary services using Docker Compose, run the test scenarios and then stop everything.)
