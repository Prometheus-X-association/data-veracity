import html
import json
from typing import Any

from jsonschema import ValidationError, FormatChecker, validate as jsvalidate

from ..model import JSONSchemaValidationResult

#initializing the global format checker
global_format_checker = FormatChecker()

def validate(data: Any, schema: str) -> JSONSchemaValidationResult:
    # TODO: Do we want to allow loading from arbitrary URL?
    # TODO: Can we eliminate this unescape?
    schema = json.loads(html.unescape(schema))

    try:
        jsvalidate(instance=data, schema=schema, format_checker=global_format_checker)
    except ValidationError as e:
        # FIX 1: Wrap 'e' in str() so Pydantic receives a string, not an object
        return JSONSchemaValidationResult(success=False, errors=str(e))

    # FIX 2: Pass an empty string "" instead of None
    return JSONSchemaValidationResult(success=True, errors="")
