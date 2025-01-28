import json

from types import SimpleNamespace


def parse_aov_req_json(aov_req_json):
    return json.loads(aov_req_json,
                      object_hook=lambda j: SimpleNamespace(**j))
