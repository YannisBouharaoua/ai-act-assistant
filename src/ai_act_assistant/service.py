"""Façade utilisée par l'API et la ligne de commande."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from .audit import AuditLog
from .config import Settings
from .corpus import load_corpus
from .graph import build_graph
from .llm import LLM, build_llm
from .retriever import Retriever, SentenceTransformerEmbedder

Decision = Literal["approve", "edit", "reject"]


class NotPendingError(Exception):
    """La conversation n'existe pas ou n'attend pas de relecture."""


class Assistant:
    def __init__(
        self,
        settings: Settings | None = None,
        llm: LLM | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.settings.state_dir.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.settings.audit_path)
        embedder = (
            SentenceTransformerEmbedder(self.settings.dense_model)
            if self.settings.dense_model
            else None
        )
        self.retriever = Retriever(load_corpus(self.settings.corpus_path), embedder)
        if checkpointer is None:
            conn = sqlite3.connect(self.settings.checkpoint_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
        self.llm = llm or build_llm(self.settings)
        self.graph = build_graph(
            self.llm, self.retriever, self.audit, checkpointer, top_k=self.settings.top_k
        )

    @staticmethod
    def _config(thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    def _pending_payload(self, thread_id: str) -> dict[str, Any] | None:
        snapshot = self.graph.get_state(self._config(thread_id))
        for task in snapshot.tasks:
            if task.interrupts:
                return task.interrupts[0].value
        return None

    def _result(self, thread_id: str) -> dict[str, Any]:
        pending = self._pending_payload(thread_id)
        if pending is not None:
            # Le brouillon n'est pas renvoyé au demandeur tant qu'il n'est pas validé.
            return {
                "thread_id": thread_id,
                "status": "pending_review",
                "answer": None,
                "citations": [],
                "sources": [],
                "review_reason": pending["reason"],
            }
        values = self.graph.get_state(self._config(thread_id)).values
        if "status" not in values:
            raise KeyError(thread_id)
        cited = set(values.get("citations", []))
        return {
            "thread_id": thread_id,
            "status": values["status"],
            "answer": values["answer"],
            "citations": values.get("citations", []),
            "sources": [c for c in values.get("chunks", []) if c["ref"] in cited],
            "review_reason": values.get("review_reason"),
        }

    def ask(self, question: str) -> dict[str, Any]:
        thread_id = uuid.uuid4().hex
        self.graph.invoke(
            {"thread_id": thread_id, "question": question.strip()}, self._config(thread_id)
        )
        result = self._result(thread_id)
        if result["status"] == "pending_review":
            self.audit.record(thread_id, "review_requested", reason=result["review_reason"])
        return result

    def get(self, thread_id: str) -> dict[str, Any]:
        return self._result(thread_id)

    def pending(self, thread_id: str) -> dict[str, Any]:
        payload = self._pending_payload(thread_id)
        if payload is None:
            raise NotPendingError(thread_id)
        return {"thread_id": thread_id, **payload}

    def review(
        self,
        thread_id: str,
        decision: Decision,
        reviewer: str,
        answer: str | None = None,
        comment: str = "",
    ) -> dict[str, Any]:
        if self._pending_payload(thread_id) is None:
            raise NotPendingError(thread_id)
        if decision == "edit" and not (answer and answer.strip()):
            raise ValueError("Une décision « edit » doit fournir la réponse corrigée.")
        resume = {
            "decision": decision,
            "reviewer": reviewer,
            "answer": (answer or "").strip(),
            "comment": comment,
        }
        self.graph.invoke(Command(resume=resume), self._config(thread_id))
        return self._result(thread_id)
