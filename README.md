# Data veracity assurance BB

The Data Veracity Assurance (DVA) building block allows data exchange participants to agree on and later prove/verify quality requirements or properties of the exchanged data.

## Design Document

See the design document [here](docs/design-document.md).

## Building instructions

At the moment, DVA has two subcomponents which must be both running: the API server and the processing module.
These can be found in the `dva-api/` and `dva-processing` subdirectories, respectively.

Both have been prepared for containerization using Docker but note that the build context must be the root of the repository.
You can use the following commands to build the images:

```console
$ docker buildx build -t dva-api:latest -f dva-api/Dockerfile ./
$ docker buildx build -t dva-processing:latest -f dva-processing/Dockerfile ./
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

By default, the test environment will include only what is strictly necessary for the DVA BB: `dva-api`, `dva-processing`, and a `rabbitmq` instance.

In addition, the following Docker Compose profiles are also available:

* `dev`: also includes a `callback-dummy` component that can be used to verify callbacks sent by `dva-api` (used in Karate-based tests).  
   Use `docker compose --profile dev up --detach` to start a test environment with a `callback-dummy`.
* `karate`: in addition to `dev`, this also includes an ephemeral `karate` container that executes availble Karate tests.  
   Use `docker compose --profile karate up --detach` to start a test environment and run all Karate tests.
   Check the `karate` container’s logs and/or the `karate-reports/` directory inside `test-env/` to analyze the results.

## Example usage

> [!TIP]
> More detailed test definitions can be found [here](docs/test-definitions.md).

The currently implemented endpoints are `/template` and `/attestation`.
See the [OpenAPI specification](docs/spec/openapi.yaml) for more information.

> [!NOTE]
> By default, the API is available at **`http://127.0.0.1:9090`** when using the [test environment](test-env/) with the default settings.
> All endpoints in the table below are relative to this URL.

> [!TIP]
> * Example **input** data can be found in [`test-env/test-data/`](test-env/test-data/).
> * Example **output** data can be found in [`test-env/example-outputs/`](test-env/example-outputs/).

Example requests to test functionality manually:

| Endpoint         | HTTP Method | Example parameters                             | Example input (request body)                                    | Expected output                                                                                                                                                                                                  |
|------------------|-------------|------------------------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/template`      | `GET`       | *nothing*                                      | *empty*                                                         | `200 OK` and a [list of VLA templates](test-env/example-outputs/template-get.json)                                                                                                                               |
| `/template`      | `POST`      | *nothing*                                      | a [VLA template](test-env/test-data/vla-template/template.json) | `201 CREATED` and [an ID](test-env/example-outputs/id-template.json)                                                                                                                                             |
| `/template/{id}` | `GET`       | `id`: a VLA template ID (eg `template-test-0`) | *empty*                                                         | `200 OK` and the requested VLA template ([example for `template-test-0`](test-env/example-outputs/template-id-get.json))                                                                                         |
| `/template/{id}` | `DELETE`    | `id`: a VLA template ID (eg `template-test-0`) | *empty*                                                         | `200 OK`                                                                                                                                                                                                         |
| `/attestation`   | `POST`      | *nothing*                                      | an [AoV request](test-env/test-data/aov/request-good.json)      | `200 OK` and [an ID](test-env/example-outputs/id-aov_request.json); also, callback with an [AoV](test-env/example-outputs/aov-callback.json) should eventually be made to `$.callbackURL` in the input JSON data |

> [!NOTE]
> AoV requests (`POST /attestation`) are processed asynchronously.
> So you should simply receive an ID in a `200 OK` response but also later receive a callback to the URL you specified from the DVA processing module.


## Unit testing

### DVA API (`dva-api`)

#### Setup test environment

_No setup needed._

#### Run tests

Set your working directory to `dva-api/` and execute:
```console
$ ./gradlew test
```

#### Expected results

In the test output, you should see all JUnit tests passing.

<details>
  <summary>Example output segment (click to open)</summary>

  ```
  [...]
  ApplicationTest > should respond with not found error on nonexistent path requested() PASSED
  AoVRoutesTest > should create attestation request() PASSED
  DocRoutesTest > should return swagger documentation page when slash swagger is requested() PASSED
  DocRoutesTest > should return HTML page when root route is requested() PASSED
  TemplateRoutesTest > should delete existing template() PASSED
  TemplateRoutesTest > should not allow creation of template with existing ID() PASSED
  TemplateRoutesTest > should respond with not found error when attempting to read nonexistent template() PASSED
  TemplateRoutesTest > should respond with list of templates() PASSED
  TemplateRoutesTest > should create new template() PASSED
  TemplateRoutesTest > should respond with not found error when attempting to delete nonexistent () PASSED
  TemplateRoutesTest > should respond with existing template if exists() PASSED
  [...]
  ```
</details>

### DVA Processing Module (`dva-processing`)

> [!WARNING]
> `dva-processing` does not -have unit tests yet.


## Component-level testing

### Setup test environment

_No setup needed, but you need to have Docker- and Docker Compose installed._

### Run tests

Change your working directory to `test-env/` and run the following:

```console
$ docker compose --profile karate up
```

### Expected results

All container should start successfully and the `karate` container should exit with code `0`.
`karate`’s summary table in the log should show the same number next to `scenarios` as `passed` (ie, all scenarios pass).

<details>
  <summary>Click to see any example of <code>karate</code>’s summary table</summary>

  ```
  karate-1  | Karate version: 1.5.0
  karate-1  | ======================================================
  karate-1  | elapsed:   2.84 | threads:    1 | thread time: 1.64
  karate-1  | features:     2 | skipped:    0 | efficiency: 0.58
  karate-1  | scenarios:    4 | passed:     4 | failed: 0
  karate-1  | ======================================================
  karate-1  |
  karate-1  | HTML report: (paste into browser to view) | Karate version: 1.5.0
  karate-1  | file:///app/target/karate-reports/karate-summary.html
  karate-1  | ===================================================================
  ```
</details>

In addition, you can check `karate` test results by checking the files generated in `test-env/karate-reports/`, such as `karate-summary.html` – you can open this in a browser.
