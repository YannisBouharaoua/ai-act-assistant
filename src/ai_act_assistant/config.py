"""Configuration lue dans l'environnement (ou un fichier .env)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["fake", "anthropic", "azure_openai"] = "fake"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5-5"

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str = "2024-10-21"

    corpus_path: Path = Path("data/sample/ai_act_sample.md")
    top_k: int = 4
    dense_model: str | None = None

    state_dir: Path = Path("var")
    reviewer_api_key: str | None = None

    @property
    def audit_path(self) -> Path:
        return self.state_dir / "audit.jsonl"

    @property
    def checkpoint_path(self) -> Path:
        return self.state_dir / "checkpoints.sqlite"
