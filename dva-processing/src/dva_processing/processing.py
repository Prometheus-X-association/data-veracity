import json
from os import environ
from typing import Any

import psycopg as pg
import requests

from .config import PG_PASS, PG_URL, PG_USER
from .eval import eval_requirement
from .log import get_logger
from .model import (
    AoVGenerationRequest,
    AoVGenerationRequestPayload,
    AoVRequest,
    EvaluateBatchRequest,
    EvaluationFromTemplateRequest,
    EvaluationRequest,
    EvaluationResult,
    QualityEngine,
    Requirement,
)
from .util import now

logger = get_logger()


def handle_eval_request(request: EvaluationRequest) -> EvaluationResult:
    logger.debug("Handling an evaluation request", request=request)
    try:
        return eval_requirement(request.data, request.requirement)
    except Exception as e:
        return EvaluationResult(
            engine=request.requirement.engine,
            timestamp=now(),
            success=False,
            details=None,
            error=str(e),
        )


def _eval_one(data: Any, requirement_dict: dict[str, Any]) -> EvaluationResult:
    try:
        requirement = Requirement(**requirement_dict)
        return eval_requirement(data, requirement)
    except Exception as e:
        logger.warning(
            "An error was thrown during evaluation of a requirement; tolerating",
            error=e,
        )
        return EvaluationResult(
            engine=None, timestamp=now(), success=False, error=str(e)
        )


def handle_eval_batch_request(request: EvaluateBatchRequest) -> list[EvaluationResult]:
    vla: dict[str, Any] = request.vla or {}

    schema_items: list[Any] = []
    raw_schema = vla.get("schema")
    if isinstance(raw_schema, list):
        schema_items = raw_schema
    elif isinstance(raw_schema, dict):
        schema_items = [raw_schema]

    results: list[EvaluationResult] = []
    any_evaluations = False

    for schema_item in schema_items:
        if not isinstance(schema_item, dict):
            continue
        quality = schema_item.get("quality") or []
        if not isinstance(quality, list):
            continue
        for requirement_dict in quality:
            any_evaluations = True
            results.append(_eval_one(request.data, requirement_dict))

    if not any_evaluations:
        top_quality = vla.get("quality")
        if isinstance(top_quality, list):
            for requirement_dict in top_quality:
                any_evaluations = True
                results.append(_eval_one(request.data, requirement_dict))
        elif isinstance(top_quality, dict):
            any_evaluations = True
            results.append(_eval_one(request.data, top_quality))

    if not any_evaluations:
        logger.warning("Nothing was evaluated from this VLA")

    return results


class TemplateNotFoundError(Exception):
    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Template {template_id} not found at the VLA Manager API")


def handle_eval_from_template_request(
    request: EvaluationFromTemplateRequest,
) -> EvaluationResult:
    vla_manager_url = environ.get("DVA_VLA_MANAGER_URL", "http://localhost:8000")
    try:
        template_id = request.template_id
        resp = requests.get(f"{vla_manager_url}/template/{template_id}", timeout=10)
        if resp.status_code == 404:
            raise TemplateNotFoundError(template_id)
        resp.raise_for_status()
        template = resp.json()
    except TemplateNotFoundError:
        raise
    except Exception as e:
        return EvaluationResult(
            engine=None, timestamp=now(), success=False, error=str(e)
        )

    em = template["evaluationMethod"]
    try:
        import chevron

        rendered = chevron.render(
            em["implementationTemplate"], request.template_model
        )
    except Exception as e:
        return EvaluationResult(
            engine=None, timestamp=now(), success=False,
            error=f"Failed to render template: {e}",
        )

    try:
        engine = QualityEngine(em["engine"].upper())
    except ValueError:
        return EvaluationResult(
            engine=None, timestamp=now(), success=False,
            error=f"Unknown engine '{em['engine']}' in template",
        )

    requirement = Requirement(implementation=rendered, engine=engine)
    return eval_requirement(request.data, requirement)


def handle_aov_request(request: AoVRequest) -> AoVGenerationRequest:
    logger.debug("Handling an AoV request", request=request)
    contract: dict[str, Any] = request.contract

    if "vla" not in contract or "schema" not in contract["vla"]:
        logger.warning("No VLA in contract or no requirements in VLA; ignoring")
        return None

    # Evaluate all requirements
    results: list[EvaluationResult] = []
    any_evaluations = False
    if len(contract["vla"]["schema"]) == 0:
        logger.warning("No schema items found in VLA")
    for schema_item in contract["vla"]["schema"]:
        if "quality" not in schema_item:
            continue

        requirement_dict: dict
        for requirement_dict in schema_item["quality"]:
            any_evaluations = True
            try:
                requirement = Requirement(**requirement_dict)
                result: EvaluationResult = eval_requirement(request.data, requirement)
            except Exception as e:
                logger.warning(
                    "An error was thrown the evaluation of a requirement; tolerating",
                    error=e,
                )
                result = EvaluationResult(
                    engine=None, timestamp=now(), success=False, error=str(e)
                )
            finally:
                results.append(result)

    if not any_evaluations:
        logger.warning("Nothing was evaluated from this VLA")

    all_success: bool = all(x.success for x in results)

    # Log evaluation results to psql database
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
                    all_success,
                    now().isoformat(),
                    json.dumps([r.model_dump_json() for r in results]),
                    request.id,
                ),
            )
        logger.info(
            f"Successfully updated PostgreSQL entry for request {request.id}",
            overall_result=all_success,
            request_id=request.id,
        )
    except Exception as e:
        logger.error(
            f"Failed to update request log entry for request {request.id}", error=e
        )

    # Return AoV generation request for ACA-Py
    return AoVGenerationRequest(
        request_id=request.id,
        exchange_id=request.exchangeID,
        contract_id=contract["id"],
        subject=contract["dataProvider"],
        issuer_id=request.attesterID,
        payload=AoVGenerationRequestPayload(
            success=all_success,
            results=results,
        ),
        target="self",
    )
