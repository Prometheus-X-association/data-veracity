from typing import Any

import jq

from ..model import JQResult


def compile_expression(query_str: str) -> "jq._Program":
    """Compile a JQ expression without running it."""
    return jq.compile(query_str)


def eval_expression(data: Any, query_str: str) -> list[JQResult]:
    query: jq._Program = compile_expression(query_str)
    # NOTE: We are expecting JQ queries to return JQResults
    return [JQResult(**x) for x in query.input(data)]
