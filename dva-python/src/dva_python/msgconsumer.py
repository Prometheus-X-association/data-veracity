import json
import requests
import sys
import uuid

from datetime import datetime

from pika import BlockingConnection, ConnectionParameters
from structlog import get_logger

from .serialization import parse_aov_req_json
from .config import ATTESTATION_QUEUE_NAME, VERIFICATION_QUEUE_NAME, RABBITMQ_HOST
from .qc import validate_data

logger = get_logger()


def run():
    try:
        consume_loop()
    except KeyboardInterrupt:
        logger.info("Exiting due to keyboard interrupt")
        sys.exit(0)


def consume_loop():
    conn = BlockingConnection(ConnectionParameters(RABBITMQ_HOST))
    chan = conn.channel()
    chan.queue_declare(queue=ATTESTATION_QUEUE_NAME)
    chan.queue_declare(queue=VERIFICATION_QUEUE_NAME)

    def attest_callback(chan, method, props, body):
        req = parse_aov_req_json(body)
        logger.info(f"Received request", callback_url=req.callbackURL)

        data_bytes = bytearray(req.data)
        data_string = data_bytes.decode(encoding='utf-8')
        logger.debug(f"Data in request: {data_string}",
                     request_data=data_string)

        mapping = req.mapping

        contract = req.contract
        vla = contract.vla
        try:
            results = validate_data(json.loads(data_string), vars(mapping), vla)
            if results['success']:
                logger.info("Successful validation", results=results)
            else:
                logger.warning("Failed validation", results=results)
            aov = {
                'aovID': uuid.uuid4(),
                'contractID': uuid.uuid4(),
                'evaluations': [],
                'vc': {
                    'id': uuid.uuid4(),
                    'type': 'VerifiableCredential',
                    'validFrom': datetime.now().isoformat(),
                    'subject': {
                        'id': contract.dataProvider,
                    },
                    'issuer': req.attesterID,
                }
            }
            requests.post(req.callbackURL, data=aov)
        except Exception as ex:
            logger.error(f"validation failed due to {ex}")
            requests.post(f'{req.callbackURL}/error')


    chan.basic_consume(queue=ATTESTATION_QUEUE_NAME,
                       auto_ack=True,
                       on_message_callback=attest_callback)

    logger.info("Waiting for new messages")


    

    def verify_callback(chan, method, props, body):
        
        logger.info(f"Received AoV/PoV verification request")

        
    chan.basic_consume(queue=VERIFICATION_QUEUE_NAME,
                       auto_ack=True,
                       on_message_callback=verify_callback)

    logger.info("Waiting for verification messages")
    chan.start_consuming()
