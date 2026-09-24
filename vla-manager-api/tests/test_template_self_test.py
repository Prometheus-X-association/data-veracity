"""
Tests for self-testing template assistant proposals.

A proposal is rendered with its exampleModel and run over its own examples
before the author sees it; one that fails gets a single correction round.
The model and DVA Processing are both faked: the model answers from a
script, processing judges each example with a function.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import (
    get_repo,
    get_requirement_evaluator,
    get_template_repo,
)
from vla_manager_api.main import create_app
from vla_manager_api.models import QualityEngine
from vla_manager_api.template_repo import FakeTemplateRepo
from vla_manager_api.validation import ProcessingError
from vla_manager_api.vla_repo import FakeVLARepo

BROKEN = "{success: (.v <= {{{max}}})}"
FIXED = '{success: (.v <= {{{max}}}), details: "checked"}'


def reply(implementation: str, **extra: Any) -> str:
    """A template assistant answer proposing a jq range check."""
    body: dict[str, Any] = {
        "message": "Here is a range check.",
        "proposal": {
            "name": "Range check",
            "criterionType": "IN_RANGE",
            "targetAspect": "ACCURACY",
            "evaluationMethod": {
                "engine": "JQ",
                "variableSchema": {
                    "type": "object",
                    "properties": {"max": {"type": "integer"}},
                    "required": ["max"],
                },
                "implementationTemplate": implementation,
            },
        },
        "examples": {"passing": [{"v": 1}, {"v": 5}], "failing": [{"v": 9}]},
        "exampleModel": {"max": 5},
    }
    body.update(extra)
    return json.dumps(body)


class ScriptedModel:
    """Answers each chat completion with the next scripted reply."""

    def __init__(self) -> None:
        self.replies: list[str] = []
        self.calls: list[list[dict[str, str]]] = []

    async def __call__(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.replies.pop(0)


class JudgingProcessing:
    """
    Runs the rendered range check the way processing would: without
    ``details`` the result is rejected; otherwise ``.v <= max``.
    """

    def __init__(self) -> None:
        self.runs: list[tuple[str, Any]] = []
        self.unreachable = False
        self.judge: Callable[[str, Any], tuple[int, Any]] = self._range_check

    @staticmethod
    def _range_check(implementation: str, data: Any) -> tuple[int, Any]:
        if "details" not in implementation:
            return 500, {"success": False, "error": "details: Field required"}
        limit = int(implementation.split("<=")[1].split(")")[0])
        return 200, {"success": data["v"] <= limit, "details": "checked"}

    async def evaluate(
        self, engine: QualityEngine, implementation: str, data: Any
    ) -> tuple[int, Any]:
        self.runs.append((implementation, data))
        if self.unreachable:
            raise ProcessingError("processing is down")
        return self.judge(implementation, data)


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> ScriptedModel:
    scripted = ScriptedModel()
    monkeypatch.setattr("vla_manager_api.assistant_routes.complete_assistant", scripted)
    return scripted


@pytest.fixture
def processing() -> JudgingProcessing:
    return JudgingProcessing()


@pytest.fixture
def client(processing: JudgingProcessing) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: FakeVLARepo()
    app.dependency_overrides[get_template_repo] = lambda: FakeTemplateRepo()
    app.dependency_overrides[get_requirement_evaluator] = lambda: processing
    with TestClient(app) as test_client:
        yield test_client


def ask(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/assistant/template", json={"message": "Values must be at most 5."}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_a_proposal_that_passes_its_examples_is_returned_as_is(
    client: TestClient, model: ScriptedModel, processing: JudgingProcessing
) -> None:
    model.replies = [reply(FIXED)]

    body = ask(client)

    assert body["selfTest"] == {"status": "passed", "problems": [], "attempts": 1}
    assert len(model.calls) == 1
    # Rendered with exampleModel, run over every example.
    assert processing.runs == [
        ('{success: (.v <= 5), details: "checked"}', {"v": 1}),
        ('{success: (.v <= 5), details: "checked"}', {"v": 5}),
        ('{success: (.v <= 5), details: "checked"}', {"v": 9}),
    ]
    assert body["exampleModel"] == {"max": 5}


def test_a_failing_proposal_is_sent_back_once_with_its_problems(
    client: TestClient, model: ScriptedModel
) -> None:
    model.replies = [reply(BROKEN), reply(FIXED, message="Added details.")]

    body = ask(client)

    assert body["selfTest"] == {"status": "passed", "problems": [], "attempts": 2}
    assert body["message"] == "Added details."
    assert body["proposal"]["evaluationMethod"]["implementationTemplate"] == FIXED
    # The correction request carries the first answer and what went wrong.
    retry = model.calls[1]
    assert retry[:-2] == model.calls[0]
    assert retry[-2] == {"role": "assistant", "content": reply(BROKEN)}
    assert retry[-1]["role"] == "user"
    assert "failed its self-test" in retry[-1]["content"]
    assert 'passing example {"v": 1} could not be evaluated' in retry[-1]["content"]
    assert "details: Field required" in retry[-1]["content"]


def test_a_proposal_still_failing_after_its_correction_is_shown_with_the_problems(
    client: TestClient, model: ScriptedModel, processing: JudgingProcessing
) -> None:
    # The corrected logic runs but gets the failing example wrong.
    processing.judge = lambda implementation, data: (
        200,
        {"success": True, "details": "always passes"},
    )
    model.replies = [reply(FIXED), reply(FIXED, message="Tried again.")]

    body = ask(client)

    assert body["selfTest"]["status"] == "failed"
    assert body["selfTest"]["attempts"] == 2
    assert body["message"] == "Tried again."
    assert body["selfTest"]["problems"] == [
        'The failing example {"v": 9} should fail but it passed (details: always passes)'
    ]
    assert len(model.calls) == 2


def test_an_unusable_correction_leaves_the_first_proposal_with_its_problems(
    client: TestClient, model: ScriptedModel
) -> None:
    model.replies = [reply(BROKEN), "not json"]

    body = ask(client)

    assert body["selfTest"]["status"] == "failed"
    assert body["selfTest"]["attempts"] == 2
    assert body["proposal"]["evaluationMethod"]["implementationTemplate"] == BROKEN


def test_an_unreachable_processing_leaves_the_proposal_untested(
    client: TestClient, model: ScriptedModel, processing: JudgingProcessing
) -> None:
    processing.unreachable = True
    model.replies = [reply(BROKEN)]

    body = ask(client)

    assert body["selfTest"]["status"] == "unavailable"
    # Nothing to correct against, so no second call.
    assert len(model.calls) == 1


@pytest.mark.parametrize(
    ("extra", "problem"),
    [
        ({"exampleModel": {"max": "five"}}, "exampleModel does not match"),
        ({"examples": None}, "No passing or failing examples"),
        ({"exampleModel": None}, "exampleModel does not match"),
    ],
)
def test_a_proposal_that_cannot_be_run_counts_as_failed(
    client: TestClient,
    model: ScriptedModel,
    processing: JudgingProcessing,
    extra: dict[str, Any],
    problem: str,
) -> None:
    model.replies = [reply(FIXED, **extra), reply(FIXED, **extra)]

    body = ask(client)

    assert body["selfTest"]["status"] == "failed"
    assert problem in body["selfTest"]["problems"][0]
    assert processing.runs == []


def test_a_reply_without_a_proposal_is_not_tested(
    client: TestClient, model: ScriptedModel, processing: JudgingProcessing
) -> None:
    model.replies = [json.dumps({"message": "Which field should it check?"})]

    body = ask(client)

    assert body["selfTest"] == {"status": "skipped", "problems": [], "attempts": 1}
    assert processing.runs == []
