import json
import yaml
import pandas as pd

from types import SimpleNamespace

from jsonpath_ng import parse


def parse_aov_req_json(aov_req_json):
    return json.loads(aov_req_json, object_hook=lambda j: SimpleNamespace(**j))


def parse_ge_yaml(ge_yaml):
    return SimpleNamespace(**(yaml.safe_load(ge_yaml)))


def json_to_df(json_dict, mapping):
    df_dict = {}
    for jsonpath_str, column_name in mapping.items():
        jsonpath = parse(jsonpath_str)
        matches = jsonpath.find(json_dict)
        if len(matches) == 0:
            raise Exception(
                f"""
                No matches found for JSONPath expression {jsonpath_str}
                """
            )
        df_dict[column_name] = [matches[0].value]

    df = pd.DataFrame.from_dict(df_dict)
    return df
