import great_expectations as gx
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
import pandas as pd

from types import SimpleNamespace
from yaml import safe_load

from jsonschema import validate, ValidationError
import jq

from .log import get_logger

import requests

import validators

import html, json


logger = get_logger()


def validate_data(data, vla):
    data_df = pd.DataFrame([data])
    data_df2 = pd.json_normalize(data)
    logger.info("Mapped JSON to dataframe", dataframe=data_df)

    # Try to convert datetimes to datetimes
    for col in data_df.select_dtypes(include=["object"]).columns:
        try:
            data_df[col] = pd.to_datetime(data_df[col])
            data_df[col] = data_df[col].astype(str)
        except (ValueError, TypeError):
            pass

    for col in data_df2.select_dtypes(include=["object"]).columns:
        try:
            data_df2[col] = pd.to_datetime(data_df2[col], errors="ignore")
        except ValueError:
            pass

    ctx = gx.get_context(mode="ephemeral")
    ctx.variables.progress_bars = gx.data_context.types.base.ProgressBarsConfig(
        globally=False
    )

    data_src_name = "test_src"
    data_asset_name = "test_asset"
    batch_def_name = "test_batch"

    data_src = ctx.data_sources.add_pandas(name=data_src_name)
    data_asset = data_src.add_dataframe_asset(name=data_asset_name)
    batch_def = data_asset.add_batch_definition_whole_dataframe(name=batch_def_name)
    batch_params = {"dataframe": data_df2}

    all_results = []
    all_success = True

    for check_str, engine in [
        (q["implementation"], q["engine"])
        for q in vla["schema"]["quality"]
    ]:
        result = {"engine": engine, "details": {}}
        success = True

        if engine == "GREAT_EXPECTATIONS":
            check = SimpleNamespace(**(safe_load(check_str)))
            gx_func = getattr(gx.expectations, check.type)
            exp = gx_func(**check.kwargs)

            batch = batch_def.get_batch(batch_parameters=batch_params)
            results = batch.validate(exp)
            success = results["success"]
            result["details"] = results.to_dict()

        elif engine == "SCHEMA":
            schema = check_str
            if validators.url(schema):
                schema = requests.get(schema).json()
            else:
                schema = json.loads(html.unescape(schema))
                
            try:
                validate(instance=data_df.to_dict(orient="records")[0], schema=schema)
                success = True
                result["details"] = {
                    "message": "Successfully validated",
                    "success": success
                }
            except ValidationError as e:
                success = False
                result["details"] = {
                    "message": "Unsuccessfully validated",
                    "success": success
                }

        elif engine == "JQ":
            query = check_str
            compiled_jq = jq.compile(query)
            result_list = list(compiled_jq.input(data_df.to_dict(orient="records")[0]))
            for r in result_list:
                if r == False:
                    success = False
            result["details"] = {"jq_result": result_list}
                
        result["success"] = success
        all_results.append(result)
        all_success = all_success and success

    return {
        "success": all_success,
        "results": all_results
    }
