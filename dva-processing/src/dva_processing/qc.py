import great_expectations as gx
import html
import jq
import json
import pandas as pd
import requests
import validators

from .log import get_logger
from jsonschema import validate, ValidationError
from types import SimpleNamespace
from yaml import safe_load


logger = get_logger()


def validate_data(data, reqs):
    data_df = pd.DataFrame([data])
    logger.info("Mapped JSON to dataframe", dataframe=data_df)

    # XXX: review/revise this part
    # Try to convert datetimes to datetimes
    # for col in data_df.select_dtypes(include=["object"]).columns:
    #     try:
    #         data_df[col] = pd.to_datetime(data_df[col])
    #         data_df[col] = data_df[col].astype(str)
    #     except (ValueError, TypeError):
    #         pass
    # for col in data_df2.select_dtypes(include=["object"]).columns:
    #     try:
    #         data_df2[col] = pd.to_datetime(data_df2[col], errors="ignore")
    #     except ValueError:
    #         pass

    all_results = []
    all_success = True

    for check_str, engine in [(req["implementation"], req["engine"]) for req in reqs]:
        result = {"engine": engine, "details": {}}

        match engine:
            case "GREAT_EXPECTATIONS":
                result["success"], result["details"] = validate_data_ge(
                    data_df, check_str
                )
            case "SCHEMA":
                result["success"], result["details"] = validate_data_schema(
                    data, check_str
                )
            case "JQ":
                result["success"], result["details"] = validate_data_jq(data, check_str)

        all_results.append(result)
        all_success = all_success and result["success"]

    return {"success": all_success, "results": all_results}


def validate_data_ge(df, check_str):
    data_src_name = "dummy_source"
    data_asset_name = "dummy_asset"
    batch_def_name = "dummy_batch"

    ctx = gx.get_context(mode="ephemeral")
    ctx.variables.progress_bars = gx.data_context.types.base.ProgressBarsConfig(
        globally=False
    )

    data_src = ctx.data_sources.add_pandas(name=data_src_name)
    data_asset = data_src.add_dataframe_asset(name=data_asset_name)
    batch_def = data_asset.add_batch_definition_whole_dataframe(name=batch_def_name)
    batch_params = {"dataframe": df}

    check = SimpleNamespace(**(safe_load(check_str)))
    gx_func = getattr(gx.expectations, check.type)
    exp = gx_func(**check.kwargs)

    batch = batch_def.get_batch(batch_parameters=batch_params)
    results = batch.validate(exp)

    return results["success"], results.to_dict()


def validate_data_schema(data, schema):
    # If schema looks like a URL, resolve it, otherwise treat load it as
    # a JSON schema
    if validators.url(schema):
        schema = requests.get(schema).json()
    else:
        # XXX: Can we eliminate this unescape?
        schema = json.loads(html.unescape(schema))

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        return False, {
            "message": "Schema validation failed",
            "error": e.message,
        }

    return True, {"message": "Schema successfully validated"}


def validate_data_jq(data, query_str):
    query = jq.compile(query_str)
    result_list = list(query.input(data))
    end_result = all(r for r in result_list)
    return end_result, {"jq_result": result_list}
