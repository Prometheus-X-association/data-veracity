import requests
import sys

from time import sleep

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
    conn = connect_with_retry(ConnectionParameters(RABBITMQ_HOST))
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


def connect_with_retry(
    params,
    max_retries=-1,
    initial_delay_s=1,
    max_delay_s=60,
    backoff_multiplier=2.0,
):
    delay = initial_delay_s
    for attempt in range_or_infinity(max_retries):
        try:
            logger.debug(
                f"Connecting to RabbitMQ at {params.host}:{params.port}; attempt {attempt + 1}"
            )
            return BlockingConnection(params)
        except Exception as e:
            logger.error(f"Connection attempt failed: {type(e).__name__} -- {e}")

            if max_retries != -1 and attempt >= max_retries:
                logger.error(
                    f"Unable to connect to RabbitMQ at {params.host} after {max_retries} attempts"
                )
                raise e

            logger.debug(f"Retrying in {delay} s")
            sleep(delay)

            delay = min(delay * backoff_multiplier, max_delay_s)


def range_or_infinity(n):
    if n == -1:
        i = 0
        while True:
            yield i
            i = i + 1
    else:
        yield from range(n)
