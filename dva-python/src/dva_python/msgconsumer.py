import json
import requests
import sys
import uuid

from datetime import datetime

from pika import BlockingConnection, ConnectionParameters
from structlog import get_logger

from .serialization import parse_aov_req_json
from .config import QUEUE_NAME, RABBITMQ_HOST
from .qc import validate_data

from pymongo import MongoClient

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
    mongo_client = MongoClient("mongodb://mongo:27017")
    db = mongo_client['dva']
    collection = db['requests']

    def callback(chan, method, props, body):
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
            successful_db = False
            if results['success']:
                logger.info("Successful validation", results=results)
                successful_db = True
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

            try:
                collection.update_one(
                                { "id": req.id },
                                { "$set": { "successful": successful_db }})
            except PyMongoError as mongo_err:
                logger.error(f"error: {mongo_err} when tried to save success")
        except Exception as ex:
            logger.error(f"validation failed due to {ex}")
            requests.post(f'{req.callbackURL}/error')


    chan.basic_consume(queue=QUEUE_NAME,
                       auto_ack=True,
                       on_message_callback=callback)

    logger.info("Waiting for messages")
    chan.start_consuming()
