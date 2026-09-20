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

The template assistant is optional. To enable it, provide these variables before starting the stack:

```console
export VLA_MANAGER_AI_PROVIDER=gemini
export VLA_MANAGER_AI_API_KEY=your-key
docker compose up -d --build
```

Gemini uses Google's OpenAI-compatible endpoint and defaults to the low-cost
`gemini-3.1-flash-lite` model. For OpenAI-compatible services, set
`VLA_MANAGER_AI_PROVIDER=openai`, `VLA_MANAGER_AI_URL`, and `VLA_MANAGER_AI_MODEL`.
For Anthropic, set `VLA_MANAGER_AI_PROVIDER=anthropic`, `VLA_MANAGER_AI_URL`, and
`VLA_MANAGER_AI_MODEL`; its native Messages API is used automatically. `VLA_MANAGER_AI_URL`
may be a provider base URL or the complete endpoint URL.

The key is passed only to the VLA Manager API container. It is never included in the frontend bundle. Without these variables, the VLA Manager remains available and the assistant reports that it is not configured.

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
