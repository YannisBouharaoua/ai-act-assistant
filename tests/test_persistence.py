from ai_act_assistant.service import Assistant


def test_pending_review_survives_a_restart(settings):
    """Le relecteur peut répondre le lendemain : l'état est sur disque, pas en mémoire."""
    first = Assistant(settings)
    tid = first.ask("Notre outil trie les candidatures, est-il à haut risque ?")["thread_id"]
    del first

    second = Assistant(settings)
    assert second.get(tid)["status"] == "pending_review"
    assert second.review(tid, "approve", reviewer="r")["status"] == "answered"
