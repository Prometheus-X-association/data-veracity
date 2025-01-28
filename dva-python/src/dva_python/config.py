from os import environ as env

QUEUE_NAME = 'ATTESTATION_REQUESTS'

RABBITMQ_HOST = env.get('DVA_RABBITMQ_HOST', default='localhost')

LOG_LEVEL = env.get('DVA_LOG_LEVEL', default='info')
