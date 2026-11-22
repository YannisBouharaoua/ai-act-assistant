"""Le graphe de l'agent.

    question → tri → recherche → rédaction → vérification des citations
                 │                               │
                 └→ refus (hors sujet)           ├→ réponse finale
                                                 └→ relecture humaine → réponse finale

Deux mécanismes de contrôle encadrent le modèle :
- la vérification des citations est faite par du code, pas par le modèle : une référence
  citée qui ne figure pas dans les extraits retrouvés déclenche une nouvelle rédaction,
  puis une relecture humaine si l'erreur persiste ;
- toute qualification d'un système (interdit, haut risque…) passe par un relecteur humain.
  Le graphe s'interrompt, son état est sauvegardé, et il reprend à la décision.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from . import prompts
from .audit import AuditLog
from .corpus import extract_citations
from .llm import LLM
from .retriever import Retriever

MAX_ATTEMPTS = 2
Route = Literal["information", "qualification", "hors_sujet"]


class AgentState(TypedDict, total=False):
    thread_id: str
    question: str
    route: Route
    chunks: list[dict[str, str]]
    draft: str
    citations: list[str]
    unverified: list[str]
    attempts: int
    feedback: str
    review_reason: str
    review: dict[str, Any]
    status: Literal["answered", "refused", "rejected"]
    answer: str


def _parse_json(text: str) -> dict[str, Any]:
    """Extrait le premier objet JSON d'une sortie de modèle, même entourée de texte."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def build_graph(
    llm: LLM,
    retriever: Retriever,
    audit: AuditLog,
    checkpointer: BaseCheckpointSaver,
    top_k: int = 4,
):
    def call_llm(state: AgentState, task: str, system: str, user: str) -> str:
        start = time.perf_counter()
        output = llm.complete(task, system, user)
        audit.record(
            state["thread_id"],
            "llm_call",
            task=task,
            model=llm.name,
            duration_ms=round((time.perf_counter() - start) * 1000),
            prompt_chars=len(system) + len(user),
            output_chars=len(output),
        )
        return output

    def route_question(state: AgentState) -> AgentState:
        audit.record(state["thread_id"], "question_received", question=state["question"])
        raw = call_llm(state, "route", prompts.ROUTE_SYSTEM, state["question"])
        route = _parse_json(raw).get("route")
        if route not in ("information", "qualification", "hors_sujet"):
            route = "information"  # sortie illisible : on traite comme une question simple
        audit.record(state["thread_id"], "routed", route=route)
        return {"route": route, "attempts": 0}

    def refuse(state: AgentState) -> AgentState:
        audit.record(state["thread_id"], "refused", reason="hors_sujet")
        return {"status": "refused", "answer": prompts.REFUSAL, "citations": []}

    def retrieve(state: AgentState) -> AgentState:
        chunks = [c.to_dict() for c in retriever.search(state["question"], k=top_k)]
        audit.record(state["thread_id"], "retrieved", chunk_ids=[c["id"] for c in chunks])
        return {"chunks": chunks}

    def generate(state: AgentState) -> AgentState:
        user = prompts.user_prompt(state["question"], state["chunks"], state.get("feedback", ""))
        if state["route"] == "qualification":
            data = _parse_json(call_llm(state, "qualify", prompts.QUALIFY_SYSTEM, user))
            level = data.get("niveau", "indetermine")
            refs = [r for r in data.get("references", []) if isinstance(r, str)]
            draft = (
                f"Niveau proposé : {prompts.LEVEL_LABELS.get(level, level)}.\n"
                f"{data.get('justification', '').strip()}\n"
                f"Références : {' '.join(f'[{r}]' for r in refs) or 'aucune'}"
            )
        else:
            draft = call_llm(state, "answer", prompts.ANSWER_SYSTEM, user).strip()
        return {"draft": draft, "attempts": state.get("attempts", 0) + 1}

    def verify(state: AgentState) -> AgentState:
        allowed = {c["ref"] for c in state["chunks"]}
        cited = extract_citations(state["draft"])
        unverified = [r for r in cited if r not in allowed]
        problem = ""
        if unverified:
            problem = (
                f"Références absentes des extraits : {', '.join(unverified)}. "
                "Ne cite que les références fournies."
            )
        elif not cited and state["chunks"]:
            problem = "Aucune source citée. Cite la référence de chaque affirmation."
        audit.record(
            state["thread_id"],
            "citations_checked",
            cited=cited,
            unverified=unverified,
            attempt=state["attempts"],
            ok=not problem,
        )
        return {"citations": cited, "unverified": unverified, "feedback": problem}

    def after_verify(state: AgentState) -> str:
        if state["feedback"] and state["attempts"] < MAX_ATTEMPTS:
            return "generate"
        if state["feedback"] or state["route"] == "qualification":
            return "human_review"
        return "finalize"

    def human_review(state: AgentState) -> AgentState:
        reason = "citations_non_verifiees" if state["feedback"] else "qualification_d_un_systeme"
        # À la reprise, LangGraph rejoue ce nœud depuis le début : tout ce qui précède
        # interrupt() doit donc être sans effet de bord.
        decision = interrupt(
            {
                "reason": reason,
                "question": state["question"],
                "draft": state["draft"],
                "citations": state["citations"],
                "unverified": state["unverified"],
                "sources": state["chunks"],
            }
        )
        audit.record(
            state["thread_id"],
            "human_review",
            reason=reason,
            decision=decision["decision"],
            reviewer=decision["reviewer"],
            comment=decision.get("comment", ""),
            edited=decision["decision"] == "edit",
        )
        return {"review_reason": reason, "review": decision}

    def finalize(state: AgentState) -> AgentState:
        review = state.get("review")
        if review and review["decision"] == "reject":
            answer = prompts.REJECTED
            status = "rejected"
            citations: list[str] = []
        else:
            body = review["answer"] if review and review["decision"] == "edit" else state["draft"]
            citations = extract_citations(body)
            answer = f"{body}\n\n{prompts.DISCLAIMER}"
            status = "answered"
        audit.record(state["thread_id"], "answered", status=status, citations=citations)
        return {"status": status, "answer": answer, "citations": citations}

    g = StateGraph(AgentState)
    g.add_node("route_question", route_question)
    g.add_node("refuse", refuse)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate)
    g.add_node("verify", verify)
    g.add_node("human_review", human_review)
    g.add_node("finalize", finalize)

    g.add_edge(START, "route_question")
    g.add_conditional_edges(
        "route_question",
        lambda s: "refuse" if s["route"] == "hors_sujet" else "retrieve",
        ["refuse", "retrieve"],
    )
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", "verify")
    g.add_conditional_edges("verify", after_verify, ["generate", "human_review", "finalize"])
    g.add_edge("human_review", "finalize")
    g.add_edge("refuse", END)
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)
