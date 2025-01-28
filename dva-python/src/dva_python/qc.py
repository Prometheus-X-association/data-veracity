import great_expectations as gx


def main():
    ctx = gx.get_context()
    data_src_name = 'test_src'
    data_src = ctx.data_sources.add_pandas(name=data_src_name)

    data_asset_name = 'test_asset'
    data_asset = data_src.add_dataframe_asset(name=data_asset_name)

    batch_def_name = 'test_batch'
    batch_def = data_asset.add_batch_definition_whole_dataframe(name=batch_def_name)

    batch_params = { 'dataframe': 


if __name__ == '__main__':
    main()
