import great_expectations as gx

from structlog import get_logger

from .serialization import json_to_df, parse_ge_yaml

logger = get_logger()


def validate_data(data_str, mapping, vla):
    data_df = json_to_df(data_str, mapping)
    print(data_df)

    ctx = gx.get_context()

    data_src_name = 'test_src'
    data_asset_name = 'test_asset'
    batch_def_name = 'test_batch'

    data_src = ctx.data_sources.add_pandas(name=data_src_name)
    data_asset = data_src.add_dataframe_asset(name=data_asset_name)
    batch_def = data_asset.add_batch_definition_whole_dataframe(name=batch_def_name)
    batch_params = { 'dataframe': data_df }

    for check_str in [q.implementation
                  for q in vla.schema[0].quality # XXX
                  if q.engine == 'greatExpectations']:
        check = parse_ge_yaml(check_str)
        gx_func = getattr(gx.expectations, check.type)
        exp = gx_func(**check.kwargs)

        batch = batch_def.get_batch(batch_parameters=batch_params)

        results = batch.validate(exp)
        break # FIXME

    return results


if __name__ == '__main__':
    main()
