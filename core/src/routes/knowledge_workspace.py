from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.executive.conversation import (
    ExecutiveConversationAdapter,
    WorkspaceConversationRequest,
)
from core.src.routes.api import conversation_service


router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Workspace"])


class KnowledgeWorkspaceQuery(BaseModel):
    question: str = Field(min_length=1)
    session_id: str | None = None
    mode: str = "knowledge"
    context: dict[str, Any] = Field(
        default_factory=lambda: {"workspace": "knowledge"}
    )


@router.post("/conversation")
def knowledge_workspace_conversation(
    query: KnowledgeWorkspaceQuery,
) -> dict[str, Any]:
    adapter = ExecutiveConversationAdapter(conversation_service.ask)
    request = WorkspaceConversationRequest(
        question=query.question,
        session_id=query.session_id,
        mode=query.mode,
        context=query.context,
    )
    return adapter.execute(request).to_dict()
