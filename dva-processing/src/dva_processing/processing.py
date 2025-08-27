import json
import psycopg as pg

from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Any

from .config import PG_URL, PG_USER, PG_PASS
from .log import get_logger
from .qc import validate_data


logger = get_logger()


class AoVRequest(BaseModel):
    id: str
    exchangeID: str
    contract: dict[str, Any]
    data: Any
    attesterID: str


class AoVGenerationRequest(BaseModel):
    request_id: str
    exchange_id: str
    contract_id: str
    subject: str
    issuer_id: str
    payload: dict[str, Any]
    target: str


def handle_aov_request(req: AoVRequest) -> AoVGenerationRequest:
    contract = req.contract
    vla = contract["vla"]
    try:
        results = validate_data(req.data, vla)
        results_dict = results.to_json_dict()
        if results["success"]:
            logger.info("Successful validation", results=results_dict)
        else:
            logger.warning("Failed validation", results=results_dict)

        try:
            with pg.connect(f"{PG_URL}?user={PG_USER}&password={PG_PASS}") as conn:
                conn.execute(
                    """
                UPDATE request_logs
                SET
                  evaluation_passing = %s,
                  evaluation_date = %s,
                  evaluation_results = %s
                WHERE request_id = %s
                """,
                    (
                        results["success"],
                        datetime.now(timezone.utc),
                        json.dumps(results_dict),
                        req.id,
                    ),
                )
            logger.info(f"Successfully updated PostgreSQL entry for request {req.id}")
        except Exception as ex:
            logger.error(f"Failed to update request log entry due to {ex}", error=ex)

        return AoVGenerationRequest(
            request_id=req.id,
            exchange_id=req.exchangeID,
            contract_id=contract["id"],
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
