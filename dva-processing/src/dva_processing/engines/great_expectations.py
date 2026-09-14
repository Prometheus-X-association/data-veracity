import pandas as pd
from great_expectations import expectations, get_context
from great_expectations.core import ExpectationValidationResult
from great_expectations.data_context.types.base import ProgressBarsConfig
from great_expectations.expectations.expectation import Expectation
from pydantic_yaml import parse_yaml_raw_as

from ..model import GreatExpectationParams


class UnknownExpectationError(ValueError):
    """A requirement names an expectation Great Expectations does not define."""

    def __init__(self, expectation_type: str) -> None:
        self.expectation_type = expectation_type
        super().__init__(f"Unknown Great Expectations type: {expectation_type}")


def parse_implementation(implementation_yaml: str) -> GreatExpectationParams:
    return parse_yaml_raw_as(GreatExpectationParams, implementation_yaml)


def build_expectation(params: GreatExpectationParams) -> Expectation:
    """
    Instantiate the expectation ``params`` names, checking its kwargs.

    Building an expectation is what rejects a misspelled type or a kwarg
    it does not take, so this is both a step of evaluation and the whole
    of what static validation can check for this engine.
    """
    expectation_type = getattr(expectations, params.type, None)
    if expectation_type is None:
        raise UnknownExpectationError(params.type)
    return expectation_type(**params.kwargs)


def validate_expectation(
    df: pd.DataFrame, params: GreatExpectationParams
) -> ExpectationValidationResult:
    ctx = get_context(mode="ephemeral")
    # Disable progress bars; they pollute the logs
    ctx.variables.progress_bars = ProgressBarsConfig(globally=False)

    data_src = ctx.data_sources.add_pandas(name="request")
    data_asset = data_src.add_dataframe_asset(name="request_df")
    batch_def = data_asset.add_batch_definition_whole_dataframe(name="whole_df")
    batch_params = {"dataframe": df}

    expectation = build_expectation(params)

    batch = batch_def.get_batch(batch_parameters=batch_params)
    return batch.validate(expectation)
