import html
import json
from typing import Any

from jsonschema import ValidationError
from jsonschema import validate as jsvalidate
from jsonschema.validators import validator_for

from ..model import JSONSchemaValidationResult


def parse_schema(schema: str) -> Any:
    """Read the JSON Schema a requirement carries as its implementation."""
    # TODO: Do we want to allow loading from arbitrary URL?
    # TODO: Can we eliminate this unescape?
    return json.loads(html.unescape(schema))


def check_schema(schema: str) -> None:
    """Raise unless ``schema`` is a well-formed JSON Schema document."""
    parsed = parse_schema(schema)
    validator_for(parsed).check_schema(parsed)


def validate(data: Any, schema: str) -> JSONSchemaValidationResult:
    parsed = parse_schema(schema)

    try:
        jsvalidate(instance=data, schema=parsed)
    except ValidationError as e:
        return JSONSchemaValidationResult(success=False, errors=str(e))

    return JSONSchemaValidationResult(success=True)
