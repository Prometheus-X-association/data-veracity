from os import environ as env


# RabbitMQ queue name for AoV requests
QUEUE_NAME = "ATTESTATION_REQUESTS"

# RabbitMQ server hostname
RABBITMQ_HOST = env.get("DVA_RABBITMQ_HOST", default="localhost")

# Postgres connection data
PG_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432")
PG_USER = env.get("DVA_POSTGRES_USER", default="postgres")
PG_PASS = env.get("DVA_POSTGRES_PASSWORD", default="postgres")

# Log level (must be supported by structlog)
LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="warn")

# ACA-Py Controller URL
ACA_PY_CONTROLLER_URL = env.get("DVA_ACA_PY_CONTROLLER_URL", default="localhost:8050")


class Configuration:
    dry_run: bool
    log_level: str

    def __init__(self, dry_run=False, log_level=LOG_LEVEL):
        self.dry_run = dry_run
        self.log_level = log_level


cfg = Configuration()
