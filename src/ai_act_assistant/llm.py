"""Accès au modèle de langage, derrière une interface unique.

Le reste du code ne connaît que ``LLM.complete``. Changer de fournisseur (Anthropic,
Azure OpenAI) ne touche donc ni le graphe ni les tests. ``FakeLLM`` est déterministe :
il sert aux tests et à la démonstration hors ligne, pas à produire de vraies réponses.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from .config import Settings
from .retriever import tokenize


class LLM(Protocol):
    name: str

    def complete(self, task: str, system: str, user: str) -> str:
        """``task`` nomme l'étape appelante (route, answer, qualify) pour le journal."""


class AnthropicLLM:
    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self.name = f"anthropic:{model}"

    def complete(self, task: str, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")


class AzureOpenAILLM:
    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str) -> None:
        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            azure_endpoint=endpoint, api_key=api_key, api_version=api_version
        )
        self._deployment = deployment
        self.name = f"azure_openai:{deployment}"

    def complete(self, task: str, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


_EXTRACT = re.compile(r'<extrait ref="([^"]+)" titre="([^"]*)">\n(.*?)\n</extrait>', re.DOTALL)
_QUALIFY_HINTS = (
    "mon systeme", "notre systeme", "notre outil", "mon outil", "nous developpons",
    "nous utilisons", "nous voulons", "je developpe", "haut risque ?", "est-il interdit",
    "classer", "qualifier", "quel niveau de risque",
)  # fmt: skip
_SCOPE_HINTS = (
    "ia", "intelligence artificielle", "ai act", "reglement", "systeme", "risque", "article",
    "annexe", "biometri", "sanction", "amende", "deployeur", "fournisseur", "transparence",
    "hypertrucage", "notation", "emotion", "journaux", "donnees", "controle humain", "interdit",
    "modele", "algorithme", "chatbot", "agent conversationnel",
)  # fmt: skip


def _fold(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class FakeLLM:
    """Modèle factice, sans réseau, au comportement fixe et lisible."""

    name = "fake"

    def complete(self, task: str, system: str, user: str) -> str:
        if task == "route":
            return json.dumps({"route": self._route(user)})
        extracts = _EXTRACT.findall(user)
        if task == "qualify":
            refs = [ref for ref, _, _ in extracts[:2]]
            return json.dumps(
                {
                    "niveau": "haut_risque" if refs else "indetermine",
                    "references": refs,
                    "justification": (
                        "Proposition du modèle factice, établie à partir des premiers "
                        "extraits retrouvés."
                    ),
                },
                ensure_ascii=False,
            )
        if not extracts:
            return "Je ne trouve pas cette information dans les extraits fournis."
        # Choisit la phrase qui partage le plus de mots avec la question.
        question = set(tokenize(user.rsplit("Question :", 1)[-1]))
        candidates = [
            (len(question & set(tokenize(line))), -i, line.strip(), ref)
            for i, (ref, _, text) in enumerate(extracts)
            for line in text.splitlines()
            if line.strip()
        ]
        _, _, sentence, ref = max(candidates)
        return f"{sentence} [{ref}]"

    @staticmethod
    def _route(user: str) -> str:
        q = _fold(user)
        words = set(re.findall(r"[a-z]+", q))
        in_scope = any((h in words) if len(h) <= 3 else (h in q) for h in _SCOPE_HINTS)
        if not in_scope:
            return "hors_sujet"
        if any(h in q for h in _QUALIFY_HINTS):
            return "qualification"
        return "information"


def build_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "fake":
        return FakeLLM()
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY est requis pour LLM_PROVIDER=anthropic.")
        return AnthropicLLM(settings.anthropic_api_key, settings.anthropic_model)
    missing = [
        name
        for name, value in (
            ("AZURE_OPENAI_ENDPOINT", settings.azure_openai_endpoint),
            ("AZURE_OPENAI_API_KEY", settings.azure_openai_api_key),
            ("AZURE_OPENAI_DEPLOYMENT", settings.azure_openai_deployment),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Variables manquantes pour Azure OpenAI : {', '.join(missing)}.")
    return AzureOpenAILLM(
        settings.azure_openai_endpoint,  # type: ignore[arg-type]
        settings.azure_openai_api_key,  # type: ignore[arg-type]
        settings.azure_openai_deployment,  # type: ignore[arg-type]
        settings.azure_openai_api_version,
    )
