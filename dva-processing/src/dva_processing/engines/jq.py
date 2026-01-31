from typing import Any

import jq

from ..model import JQResult


def eval_expression(data: Any, query_str: str) -> list[JQResult]:
    query: jq._Program = jq.compile(query_str)
    # NOTE: We are expecting JQ queries to return JQResults
    return [JQResult(**x) for x in query.input(data)]
