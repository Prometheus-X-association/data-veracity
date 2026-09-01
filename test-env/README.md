# DVA Test Environment

From this directory, start the complete local environment:

```console
docker compose up -d --build
```

Wait until every service is healthy:

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
| VLA Manager API | http://localhost:8000/swagger |
| VC Manager API | http://localhost:8001/swagger |

The provider and consumer dashboards use their corresponding DVA APIs. Both dashboards also use the local VLA Manager API and VC Manager API, so the VLA list, credential history, verification history, and failure feedback can be reviewed from one running environment.

The environment follows the refactored HTTP-only architecture. It does not start RabbitMQ or ACA-Py.

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
