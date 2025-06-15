import json

from pydantic import BaseModel, PositiveInt
from typing import Any

from .log import get_logger
from .qc import validate_data


logger = get_logger()


class AoVRequest(BaseModel):
    contract: dict[str, Any]
    data: list[PositiveInt]
    attesterID: str
    callbackURL: str
    mapping: dict[str, str]


class AoVGenerationRequest(BaseModel):
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

        return AoVGenerationRequest(
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
