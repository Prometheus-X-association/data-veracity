from os import environ as env


# RabbitMQ queue name for AoV requests
QUEUE_NAME = 'ATTESTATION_REQUESTS'

# RabbitMQ server hostname
RABBITMQ_HOST = env.get('DVA_RABBITMQ_HOST', default='localhost')

# Log level (must be supported by structlog)
LOG_LEVEL = env.get('DVA_LOG_LEVEL', default='info')
