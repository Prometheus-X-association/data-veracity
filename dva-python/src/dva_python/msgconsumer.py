import requests
import sys

from pika import BlockingConnection, ConnectionParameters

from .config import QUEUE_NAME, RABBITMQ_HOST, ACA_PY_CONTROLLER_URL
from .log import get_logger
from .processing import AoVRequest, handle_aov_request

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
        aov_request = AoVRequest.model_validate_json(
            bytearray(body).decode(encoding="utf-8")
        )
        logger.info("Received AoV request", request=aov_request)
        aov_gen_req = handle_aov_request(aov_request)
        logger.info("Sending AoV VC generation request", request=aov_gen_req)
        print("AoV Generation Request as a JSON string {{{")
        print(aov_gen_req.model_dump_json())
        print("}}} ----- ")
        requests.post(
            f"{ACA_PY_CONTROLLER_URL}/generate_aov",
            json=aov_gen_req.model_dump(),
        )

    chan.basic_consume(queue=QUEUE_NAME, auto_ack=True, on_message_callback=callback)

    logger.info("Waiting for messages")
    chan.start_consuming()
