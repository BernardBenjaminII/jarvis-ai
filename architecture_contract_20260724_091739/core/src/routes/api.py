"""JARVIS command and conversation API routes."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query as FastAPIQuery
from pydantic import BaseModel, Field

from core.conversation import (
    CatalogGroundingService,
    ExecutiveConversationOrchestrator,
    ExecutiveConversationService,
)
from core.executive.director import ExecutiveDirector
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.src.brain import route_question

router = APIRouter()


def _runtime_root() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return Path(os.getenv("JARVIS_RUNTIME_ROOT", project_root / ".runtime")).expanduser()


def _conversation_database_path() -> Path:
    configured = os.getenv("JARVIS_CONVERSATION_DB")
    return Path(configured).expanduser() if configured else _runtime_root() / "conversation" / "conversation.sqlite"


def _executive_database_path() -> Path:
    configured = os.getenv("JARVIS_EXECUTIVE_DB")
    return Path(configured).expanduser() if configured else _runtime_root() / "executive" / "missions.sqlite"


def _catalog_database_path() -> Path:
    configured = os.getenv("JARVIS_CATALOG_DB")
    return Path(configured).expanduser() if configured else DEFAULT_CATALOG_DB


catalog_grounding = CatalogGroundingService(database_path=_catalog_database_path())
executive_director = ExecutiveDirector(
    database_path=_executive_database_path(),
    knowledge_search=catalog_grounding.search_for_director,
)
conversation_orchestrator = ExecutiveConversationOrchestrator(
    director=executive_director,
    synthesis_handler=route_question,
    grounding_service=catalog_grounding,
)
conversation_service = ExecutiveConversationService(
    database_path=_conversation_database_path(),
    orchestrator=conversation_orchestrator,
)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=32_000)
    mode: str = "full"


class ConversationQuery(BaseModel):
    question: str = Field(min_length=1, max_length=32_000)
    session_id: str | None = Field(default=None, max_length=128)
    mode: str = Field(default="full", max_length=64)
    channel: str = Field(default="text", max_length=64)
    metadata: dict = Field(default_factory=dict)


@router.post("/ask")
def ask(q: Query) -> dict[str, str]:
    response = conversation_service.ask(q.question, mode=q.mode)
    if response.error:
        raise HTTPException(status_code=500, detail=response.error)
    return {"response": response.answer}


@router.post("/api/conversation/query")
def conversation_query(q: ConversationQuery) -> dict:
    return conversation_service.ask(
        q.question,
        session_id=q.session_id,
        mode=q.mode,
        channel=q.channel,
        metadata=q.metadata,
    ).to_dict()


@router.get("/api/conversation/sessions/{session_id}")
def conversation_session(session_id: str) -> dict:
    session = conversation_service.repository.session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return session


@router.get("/api/conversation/sessions/{session_id}/messages")
def conversation_messages(
    session_id: str,
    limit: int = FastAPIQuery(default=100, ge=1, le=500),
) -> dict:
    session = conversation_service.repository.session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return {"session_id": session_id, "messages": conversation_service.history(session_id, limit=limit)}
