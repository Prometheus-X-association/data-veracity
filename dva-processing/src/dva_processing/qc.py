import great_expectations as gx
import pandas as pd

from types import SimpleNamespace
from yaml import safe_load

from .log import get_logger


logger = get_logger()


def validate_data(data, vla):
    data_df = pd.json_normalize(data)
    logger.info("Mapped JSON to dataframe", dataframe=data_df)

    # Try to convert datetimes to datetimes
    for col in data_df.select_dtypes(include=["object"]).columns:
        try:
            data_df[col] = pd.to_datetime(data_df[col], errors="ignore")
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
    batch_params = {"dataframe": data_df}

    for check_str in [
        q["implementation"]
        for q in vla["schema"][0]["quality"]  # XXX
        if q["engine"] == "greatExpectations"
    ]:
        check = SimpleNamespace(**(safe_load(check_str)))
        gx_func = getattr(gx.expectations, check.type)
        exp = gx_func(**check.kwargs)

        batch = batch_def.get_batch(batch_parameters=batch_params)

        results = batch.validate(exp)
        break  # FIXME

    return results
