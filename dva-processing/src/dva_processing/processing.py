import json

from datetime import datetime
from pydantic import BaseModel, PositiveInt
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Any

from .config import MONGO_URL, MONGO_DB, MONGO_COLLECTION
from .log import get_logger
from .qc import validate_data


logger = get_logger()


class AoVRequest(BaseModel):
    id: str
    contract: dict[str, Any]
    data: list[PositiveInt]
    attesterID: str
    callbackURL: str
    mapping: dict[str, str]


class AoVGenerationRequest(BaseModel):
    request_id: str
    subject: str
    issuer_id: str
    payload: dict[str, Any]
    target: str


def handle_aov_request(req: AoVRequest) -> AoVGenerationRequest:
    data_bytes = bytearray(req.data)
    data_string = data_bytes.decode(encoding="utf-8")
    logger.debug(f"Data in request: {data_string}", request_data=data_string)

    mapping = req.mapping

    contract = req.contract
    vla = contract["vla"]
    try:
        results = validate_data(json.loads(data_string), mapping, vla)
        results_dict = results.to_json_dict()
        if results["success"]:
            logger.info("Successful validation", results=results_dict)
        else:
            logger.warning("Failed validation", results=results_dict)

        try:
            req_coll = MongoClient(MONGO_URL)[MONGO_DB][MONGO_COLLECTION]
            req_coll.update_one(
                {"requestID": req.id},
                {
                    "$set": {
                        "evaluationPassing": results["success"],
                        "evaluationDate": datetime.utcnow(),
                        "evaluationResults": json.dumps(results_dict),
                    }
                },
            )
            logger.info(f"Successfully updated MongoDB entry for request {req.id}")
        except PyMongoError as e:
            logger.error(f"Failed to update MongoDB entry due to {e}", error=e)

        return AoVGenerationRequest(
            request_id=req.id,
            subject=contract["dataProvider"],
            issuer_id=req.attesterID,
            payload={
                "success": results["success"],
                "results": results_dict,
            },
            target="self",
        )
    except Exception as ex:
        logger.error(f"Validation failed due to {ex}", exception=ex)
