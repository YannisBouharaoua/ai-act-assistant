from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from ai_act_assistant.config import Settings
from ai_act_assistant.service import Assistant

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample" / "ai_act_sample.md"


class ScriptedLLM:
    """Modèle de test : renvoie, pour chaque tâche, les sorties prévues dans l'ordre."""

    name = "scripted"

    def __init__(self, **outputs: list[str]) -> None:
        self.outputs = {task: deque(values) for task, values in outputs.items()}
        self.calls: list[tuple[str, str, str]] = []

    def complete(self, task: str, system: str, user: str) -> str:
        self.calls.append((task, system, user))
        return self.outputs[task].popleft()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        llm_provider="fake",
        corpus_path=SAMPLE,
        state_dir=tmp_path / "var",
        reviewer_api_key="test-key",
    )


@pytest.fixture
def make_assistant(settings: Settings):
    def _make(llm=None) -> Assistant:
        return Assistant(settings, llm=llm, checkpointer=InMemorySaver())

    return _make
