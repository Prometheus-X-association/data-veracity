import html
import json
from typing import Any

import requests
import validators
from jsonschema import ValidationError, validate as jsvalidate

from ..model import JSONSchemaValidationResult


def validate(data: Any, schema: str) -> JSONSchemaValidationResult:
    # If schema looks like a URL, resolve it;
    # otherwise treat load it as a JSON schema string
    if validators.url(schema):
        schema = requests.get(schema).json()
    else:
        # TODO: Can we eliminate this unescape?
        schema = json.loads(html.unescape(schema))

    try:
        jsvalidate(instance=data, schema=schema)
    except ValidationError as e:
        return JSONSchemaValidationResult(success=False, errors=e)

    return JSONSchemaValidationResult(success=True, errors=None)
