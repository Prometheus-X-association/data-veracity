# Data veracity assurance BB

The Data Veracity Assurance (DVA) building block allows data exchange participants to agree on and later prove/verify quality requirements or properties of the exchanged data.

## Design Document

See the design document [here](docs/design-document.md).

## Building instructions

At the moment, DVA has two subcomponents which must be both running: the API server and the processing module.
These can be found in the `dva-jvm/` and `dva-python` subdirectories, respectively.

Both have been prepared for containerization using Docker but note that the build context must be the root of the repository.
You can use the following commands to build the images:

```console
$ docker buildx build -t dva-api:latest -f dva-jvm/Dockerfile ./
$ docker buildx build -t dva-processing:latest -f dva-python/Dockerfile ./
```

> [!NOTE]
> The resulting `dva-api` image currently needs to receive a command parameter when running.
> Currently, the only used parameter is `api`.

> [!IMPORTANT]
> DVA also needs other internal services to be running to work, such as a RabbitMQ instance.
> To try out the DVA component, we suggest using the test environment (see later).

## Running instructions

A test environment has been prepared in the `test-env` subdirectory.

A simple `docker compose up` should be sufficient to start the test environment.

## Example usage

> [!TIP]
> A more detailed testing guide can be found [here](docs/testing.md).

The currently implemented endpoints are `/template` and `/attestation`.
See the [OpenAPI specification](docs/spec/openapi.yaml) for more information.

> [!NOTE]
> By default, the API is available at **`http://127.0.0.1:9090`** when using the [test environment](test-env/) with the default settings.
> All endpoints in the table below are relative to this URL.

> [!TIP]
> * Example **input** data can be found in [`test-env/test-data/`](test-env/test-data/).
> * Example **output** data can be found in [`test-env/example-outputs/`](test-env/example-outputs/).

Example requests to test functionality manually:

| Endpoint         | HTTP Method | Example parameters                             | Example input (request body)                                    | Expected output                                                                                                                                                                                      |
|------------------|-------------|------------------------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/template`      | `GET`       | *nothing*                                      | *empty*                                                         | `200 OK` and a [list of VLA templates](test-env/example-outputs/template-get.json)                                                                                                                   |
| `/template`      | `POST`      | *nothing*                                      | a [VLA template](test-env/test-data/vla-template/template.json) | `201 CREATED` and [an ID](test-env/example-outputs/id.json)                                                                                                                                          |
| `/template/{id}` | `GET`       | `id`: a VLA template ID (eg `template-test-0`) | *empty*                                                         | `200 OK` and the requested VLA template ([example for `template-test-0`](test-env/example-outputs/template-id-get.json))                                                                             |
| `/template/{id}` | `DELETE`    | `id`: a VLA template ID (eg `template-test-0`) | *empty*                                                         | `200 OK`                                                                                                                                                                                             |
| `/attestation`   | `POST`      | *nothing*                                      | an [AoV request](test-env/test-data/aov/request-good.json)      | `200 OK` and [an ID](test-env/example-outputs/id.json); also, callback with an [AoV](test-env/example-outputs/aov-callback.json) should eventually be made to `$.callbackURL` in the input JSON data |

> [!NOTE]
> AoV requests (`POST /attestation`) are processed asynchronously.
> So you should simply receive an ID in a `200 OK` response but also later receive a callback to the URL you specified from the DVA processing module.

## Unit testing
### Setup test environment
### Run tests
### Expected results

## Component-level testing
### Setup test environment
### Run tests
### Expected results
