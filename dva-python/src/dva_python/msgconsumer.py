import json
import requests
import sys
import uuid

from datetime import datetime

from pika import BlockingConnection, ConnectionParameters
from structlog import get_logger

from .serialization import parse_aov_req_json
from .config import QUEUE_NAME, RABBITMQ_HOST

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
    chan.queue_declare(queue=QUEUE_NAME)

    def callback(chan, method, props, body):
        req = parse_aov_req_json(body)
        logger.info(f"Received request", callback_url=req.callbackURL)

        data_bytes = bytearray(req.data)
        data_string = data_bytes.decode(encoding='utf-8')
        logger.debug(f"Data in request: {data_string}",
                     request_data=data_string)

        contract = req.contract
        for vla in contract.vla:
            logger.debug(f"Now checking VLA element {vla.id}",
                         vla_id=vla.id)

            match vla.objective.targetAspect:
                case 'SYNTAX':
                    logger.debug(
                        f"{vla.id} is a syntax check; checking"
                    )

                    try:
                        json.loads(data_string)
                    except ValueError:
                        logger.warning(
                            f"{data_string} failed syntax check")
                        requests.post(f"{req.callbackURL}/error")

                    logger.debug(f"{data_string} passed syntax check")

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


                case _:
                    logger.warning(
                        f"""{vla.id} is for an unsupported aspect
                        {vla.objective.targetAspect}; skipping""",
                        vla_id=vla.id,
                        target_aspect=vla.objective.targetAspect
                    )



    chan.basic_consume(queue=QUEUE_NAME,
                       auto_ack=True,
                       on_message_callback=callback)

    logger.info("Waiting for messages")
    chan.start_consuming()
