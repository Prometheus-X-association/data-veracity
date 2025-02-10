# Data veracity assurance BB

The Data Veracity Assurance (DVA) building block allows data exchange participants to agree on and later prove/verify quality requirements or properties of the exchanged data.

## Design Document

See the design document [here](docs/design-document.md).

## Building instructions

At the moment, DVA has two subcomponents which must be both running: the API server and the processing module.
These can be found in the `dva-jvm/` and `dva-python` subdirectories, respectively.

Both have been prepared for containerization using Docker; i.e., you can use the following commands to build the images:

```console
$ cd /path/to/dva-jvm/
$ docker buildx build -t dva-api:latest .

$ cd /path/to/dva-python/
$ docker buildx build -t dva-processing:latest
```

> [!NOTE]
> The resulting `dva-api` image needs to receive a command parameter when running.
> Currently, the only used parameter is `api`.

> [!IMPORTANT]
> DVA also needs other internal services to be running to work, such as a RabbitMQ instance.
> To try out the DVA component, we suggest using the test environment (see later).

## Running instructions

A test environment has been prepared in the `test-env` subdirectory.

A simple `docker compose up` should be sufficient to start the test environment.

## Example usage

The currently implemented endpoints are `/template` and `/attestation`.
See the OpenAPI specification for more information.

Example requests to test functionality manually:

| Endpoint         | HTTP Method   | Example input                  | Expected output                         |
| ---------------- | ------------- | ------------------------------ | --------------------------------------- |
| `/template`      | `GET`         | N/A                            | `200 OK` and a list of VLA templates    |
| `/template`      | `POST`        | a VLA template as per the spec | `201 CREATED` and an ID                 |
| `/template/{id}` | `GET`         | `id`: A VLA template ID        | `200 OK` and the requested VLA template |
| `/template/{id}` | `DELETE`      | `id`: A VLA template ID        | `200 OK`                                |
| `/attestation`   | `POST`        | an AoV request as per the spec | `200 OK` and an ID                      |

> [!NOTE]
> AoV requests are processed asynchronously.
> So you should simply receive an ID in a `200 OK` response but also later receive a callback to the URL you specified from the DVA processing module.
