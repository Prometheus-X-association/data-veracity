# DVA API module (Kotlin)

## How to build

Execute from the parent directory (root of the repository)
```console
docker buildx build -t dva-api:latest -f dva-api/Dockerfile ./
```


## Health

`GET /livez` always passes; `GET /readyz` fails when Postgres or the `/livez` of the VLA Manager, processing or the VC Manager does not answer.
`GET /info/health` collects the `/readyz` of the gateway and of each of those services, for the dashboard.
See [`docs/health-checks.md`](../docs/health-checks.md).


## How to run unit tests

```console
./gradlew test
```

> [!TIP]
> If your goal is ultimate reproducibility, you can try the following one-liner to run unit tests in a Docker container.
> Run it from the parent directory (the repository root).
> ```console
> docker run --rm -it \
>     -v ./docs/spec/dva-api.yaml:/home/gradle/docs/spec/dva-api.yaml:ro \
>     -v ./docs/spec/components.yaml:/home/gradle/docs/spec/components.yaml:ro \
>     -v /run/docker.sock:/run/docker.sock \
>     $(docker buildx build -q --no-cache --target build -f dva-api/Dockerfile ./) \
>     gradle test
> ```
