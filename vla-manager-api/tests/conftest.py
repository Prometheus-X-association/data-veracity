"""Shared test setup."""

from __future__ import annotations

import pytest

from vla_manager_api.config import cfg


@pytest.fixture(autouse=True)
def unconfigured_assistant(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Start every test with the AI assistant unconfigured, as it is by default.

    ``cfg`` reads ``VLA_MANAGER_AI_*`` from the environment, so a developer
    who exports real credentials would otherwise have tests pick them up –
    and a test that expects the assistant to be off would send a real,
    billed request. Tests that need a provider set one explicitly.
    """
    monkeypatch.setattr(cfg, "ai_provider", "openai")
    monkeypatch.setattr(cfg, "ai_url", "")
    monkeypatch.setattr(cfg, "ai_api_key", "")
    monkeypatch.setattr(cfg, "ai_model", "")
