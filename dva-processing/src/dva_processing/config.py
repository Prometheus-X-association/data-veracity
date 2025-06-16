from os import environ as env


class Configuration:
    dry_run: bool

    def __init__(self, dry_run=False):
        self.dry_run = dry_run


cfg = Configuration()

# RabbitMQ queue name for AoV requests
QUEUE_NAME = "ATTESTATION_REQUESTS"

# RabbitMQ server hostname
RABBITMQ_HOST = env.get("DVA_RABBITMQ_HOST", default="localhost")

# MongoDB data
MONGO_URL = env.get("DVA_MONGODB_URL", default="mongodb://localhost:27017")
MONGO_DB = env.get("DVA_MONGODB_DB", default="dva")
MONGO_COLLECTION = env.get("DVA_MONGODB_COLLECTION_REQUESTS", default="requests")

# Log level (must be supported by structlog)
LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="info")

# ACA-Py Controller URL
ACA_PY_CONTROLLER_URL = env.get("DVA_ACA_PY_CONTROLLER_URL", default="localhost:8050")
