import pytest
from fastapi.testclient import TestClient

from ai_act_assistant.api import create_app

KEY = {"X-Reviewer-Key": "test-key"}
QUALIF = "Notre outil trie les candidatures pour le recrutement, est-il à haut risque ?"


@pytest.fixture
def client(make_assistant):
    with TestClient(create_app(make_assistant())) as c:
        yield c


def test_health(client):
    body = client.get("/health").json()
    assert body == {"status": "ok", "model": "fake", "chunks": 11}


def test_ask_then_read_thread(client):
    r = client.post("/ask", json={"question": "Combien de temps conserver les journaux ?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered" and body["citations"] == ["Article 26"]
    assert client.get(f"/threads/{body['thread_id']}").json() == body


def test_question_is_validated(client):
    assert client.post("/ask", json={"question": "a"}).status_code == 422
    assert client.get("/threads/inconnu").status_code == 404


def test_full_review_flow_over_http(client):
    asked = client.post("/ask", json={"question": QUALIF}).json()
    tid = asked["thread_id"]
    assert asked["status"] == "pending_review" and asked["answer"] is None

    assert client.get(f"/reviews/{tid}").status_code == 401
    assert client.get(f"/reviews/{tid}", headers={"X-Reviewer-Key": "faux"}).status_code == 401
    assert (
        client.post(f"/reviews/{tid}", json={"decision": "approve", "reviewer": "x"}).status_code
        == 401
    )

    draft = client.get(f"/reviews/{tid}", headers=KEY).json()
    assert draft["reason"] == "qualification_d_un_systeme" and "Niveau proposé" in draft["draft"]

    done = client.post(
        f"/reviews/{tid}", headers=KEY, json={"decision": "approve", "reviewer": "juriste"}
    )
    assert done.status_code == 200 and done.json()["status"] == "answered"
    assert client.get(f"/reviews/{tid}", headers=KEY).status_code == 404
    assert (
        client.post(
            f"/reviews/{tid}", headers=KEY, json={"decision": "approve", "reviewer": "juriste"}
        ).status_code
        == 404
    )

    audit = client.get(f"/audit/{tid}", headers=KEY).json()
    assert audit[-1]["event"] == "answered"
    assert client.get(f"/audit/{tid}").status_code == 401


def test_edit_without_answer_is_422(client):
    tid = client.post("/ask", json={"question": QUALIF}).json()["thread_id"]
    r = client.post(f"/reviews/{tid}", headers=KEY, json={"decision": "edit", "reviewer": "j"})
    assert r.status_code == 422


def test_review_routes_are_disabled_without_configured_key(make_assistant, settings):
    settings.reviewer_api_key = None
    with TestClient(create_app(make_assistant())) as c:
        assert c.get("/reviews/x", headers=KEY).status_code == 503
