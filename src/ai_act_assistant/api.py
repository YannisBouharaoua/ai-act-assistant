"""API HTTP.

Deux publics, deux jeux de routes :
- le demandeur pose une question et lit la réponse (/ask, /threads) ;
- le relecteur, authentifié par une clé, lit le brouillon, décide et consulte le journal
  d'audit (/reviews, /audit).
"""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from . import __version__
from .service import Assistant, NotPendingError


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class Source(BaseModel):
    id: str
    ref: str
    title: str
    text: str


class AskResponse(BaseModel):
    thread_id: str
    status: Literal["answered", "refused", "rejected", "pending_review"]
    answer: str | None
    citations: list[str]
    sources: list[Source]
    review_reason: str | None = None


class ReviewRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer: str = Field(min_length=1, max_length=100)
    answer: str | None = Field(default=None, max_length=5000)
    comment: str = Field(default="", max_length=2000)


NO_PENDING = "Aucune relecture en attente pour cette conversation."


def get_assistant(request: Request) -> Assistant:
    return request.app.state.assistant


def require_reviewer(
    request: Request, x_reviewer_key: Annotated[str | None, Header()] = None
) -> None:
    expected = request.app.state.assistant.settings.reviewer_api_key
    if not expected:
        raise HTTPException(503, "Relecture désactivée : REVIEWER_API_KEY n'est pas défini.")
    if not x_reviewer_key or not secrets.compare_digest(x_reviewer_key.encode(), expected.encode()):
        raise HTTPException(401, "Clé de relecteur absente ou invalide.")


AssistantDep = Annotated[Assistant, Depends(get_assistant)]
reviewer_only = [Depends(require_reviewer)]


def create_app(assistant: Assistant | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.assistant = assistant or Assistant()
        yield

    app = FastAPI(title="AI Act Assistant", version=__version__, lifespan=lifespan)

    @app.get("/health")
    def health(a: AssistantDep) -> dict[str, Any]:
        return {"status": "ok", "model": a.llm.name, "chunks": len(a.retriever.chunks)}

    @app.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest, a: AssistantDep) -> dict[str, Any]:
        return a.ask(body.question)

    @app.get("/threads/{thread_id}", response_model=AskResponse)
    def get_thread(thread_id: str, a: AssistantDep) -> dict[str, Any]:
        try:
            return a.get(thread_id)
        except KeyError:
            raise HTTPException(404, "Conversation inconnue.") from None

    @app.get("/reviews/{thread_id}", dependencies=reviewer_only)
    def get_review(thread_id: str, a: AssistantDep) -> dict[str, Any]:
        try:
            return a.pending(thread_id)
        except NotPendingError:
            raise HTTPException(404, NO_PENDING) from None

    @app.post("/reviews/{thread_id}", response_model=AskResponse, dependencies=reviewer_only)
    def post_review(thread_id: str, body: ReviewRequest, a: AssistantDep) -> dict[str, Any]:
        try:
            return a.review(thread_id, body.decision, body.reviewer, body.answer, body.comment)
        except NotPendingError:
            raise HTTPException(404, NO_PENDING) from None
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.get("/audit/{thread_id}", dependencies=reviewer_only)
    def get_audit(thread_id: str, a: AssistantDep) -> list[dict[str, Any]]:
        return a.audit.read(thread_id)

    return app


app = create_app()
