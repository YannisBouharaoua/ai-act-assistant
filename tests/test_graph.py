import json

import pytest

from ai_act_assistant import prompts
from ai_act_assistant.service import NotPendingError

from .conftest import ScriptedLLM

INFO = json.dumps({"route": "information"})
QUALIF = json.dumps({"route": "qualification"})


def events(assistant, thread_id):
    return [e["event"] for e in assistant.audit.read(thread_id)]


def test_information_question_is_answered_with_verified_citation(make_assistant):
    a = make_assistant()
    r = a.ask("Quelle est l'amende maximale en cas de pratique interdite ?")
    assert r["status"] == "answered"
    assert r["citations"] == ["Article 99"]
    assert [s["ref"] for s in r["sources"]] == ["Article 99"]
    assert "35 000 000" in r["answer"] and prompts.DISCLAIMER in r["answer"]
    assert events(a, r["thread_id"]) == [
        "question_received", "llm_call", "routed", "retrieved",
        "llm_call", "citations_checked", "answered",
    ]  # fmt: skip


def test_out_of_scope_question_is_refused_without_retrieval(make_assistant):
    a = make_assistant()
    r = a.ask("Quelle est la recette de la ratatouille ?")
    assert r["status"] == "refused" and r["answer"] == prompts.REFUSAL
    assert "retrieved" not in events(a, r["thread_id"])


def test_hallucinated_citation_triggers_a_retry_with_feedback(make_assistant):
    llm = ScriptedLLM(
        route=[INFO],
        answer=["Jusqu'à 35 millions d'euros [Article 71].", "Jusqu'à 35 M EUR [Article 99]."],
    )
    a = make_assistant(llm)
    r = a.ask("Quelle est l'amende maximale en cas de pratique interdite ?")
    assert r["status"] == "answered" and r["citations"] == ["Article 99"]
    assert "Article 71" in llm.calls[-1][2]  # la correction est transmise au modèle
    checks = [e for e in a.audit.read(r["thread_id"]) if e["event"] == "citations_checked"]
    assert [c["ok"] for c in checks] == [False, True]
    assert checks[0]["unverified"] == ["Article 71"]


def test_persistent_bad_citation_goes_to_human_and_draft_is_withheld(make_assistant):
    llm = ScriptedLLM(route=[INFO], answer=["Voir [Article 71].", "Voir [Article 72]."])
    a = make_assistant(llm)
    r = a.ask("Quelle est l'amende maximale en cas de pratique interdite ?")
    assert r["status"] == "pending_review"
    assert r["answer"] is None and r["sources"] == []
    assert r["review_reason"] == "citations_non_verifiees"
    pending = a.pending(r["thread_id"])
    assert pending["unverified"] == ["Article 72"] and "Article 72" in pending["draft"]
    assert len(llm.calls) == 3  # pas de troisième tentative


def test_answer_without_any_citation_is_not_accepted(make_assistant):
    llm = ScriptedLLM(route=[INFO], answer=["C'est 35 millions.", "C'est 35 millions."])
    r = make_assistant(llm).ask("Quelle est l'amende maximale en cas de pratique interdite ?")
    assert r["status"] == "pending_review"


def test_qualification_always_waits_for_a_human_then_resumes(make_assistant):
    a = make_assistant()
    r = a.ask("Notre outil trie les candidatures pour le recrutement, est-il à haut risque ?")
    assert r["status"] == "pending_review"
    assert r["review_reason"] == "qualification_d_un_systeme"
    assert a.get(r["thread_id"])["status"] == "pending_review"

    done = a.review(r["thread_id"], "approve", reviewer="juriste@example.org", comment="ok")
    assert done["status"] == "answered"
    assert "Annexe III" in done["citations"]
    log = a.audit.read(r["thread_id"])
    review = [e for e in log if e["event"] == "human_review"]
    assert len(review) == 1  # le nœud est rejoué à la reprise, pas l'écriture du journal
    assert review[0]["reviewer"] == "juriste@example.org" and review[0]["decision"] == "approve"
    assert [e["event"] for e in log].count("review_requested") == 1


def test_reviewer_can_edit_or_reject(make_assistant):
    a = make_assistant()
    q = "Notre outil trie les candidatures pour le recrutement, est-il à haut risque ?"

    t1 = a.ask(q)["thread_id"]
    edited = a.review(t1, "edit", reviewer="r", answer="Haut risque, domaine emploi [Annexe III].")
    assert edited["answer"].startswith("Haut risque, domaine emploi")
    assert edited["citations"] == ["Annexe III"]

    t2 = a.ask(q)["thread_id"]
    rejected = a.review(t2, "reject", reviewer="r")
    assert rejected["status"] == "rejected" and rejected["answer"] == prompts.REJECTED
    assert rejected["citations"] == []


def test_review_is_refused_when_nothing_is_pending(make_assistant):
    a = make_assistant()
    r = a.ask("Quelle est l'amende maximale en cas de pratique interdite ?")
    with pytest.raises(NotPendingError):
        a.review(r["thread_id"], "approve", reviewer="r")
    with pytest.raises(NotPendingError):
        a.review("inconnu", "approve", reviewer="r")


def test_edit_requires_an_answer(make_assistant):
    a = make_assistant()
    t = a.ask("Notre outil trie les candidatures, est-il à haut risque ?")["thread_id"]
    with pytest.raises(ValueError):
        a.review(t, "edit", reviewer="r", answer="  ")
    assert a.get(t)["status"] == "pending_review"


def test_unreadable_router_output_falls_back_to_information(make_assistant):
    llm = ScriptedLLM(route=["je ne sais pas"], answer=["Six mois au moins [Article 26]."])
    r = make_assistant(llm).ask("Combien de temps conserver les journaux ?")
    assert r["status"] == "answered"


def test_malformed_qualification_is_still_reviewed_not_crashed(make_assistant):
    llm = ScriptedLLM(route=[QUALIF], qualify=["pas du json", "toujours pas"])
    r = make_assistant(llm).ask("Notre système note les candidats, quel niveau de risque ?")
    assert r["status"] == "pending_review"
    assert r["review_reason"] == "citations_non_verifiees"
