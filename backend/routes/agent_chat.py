""" LangGraph Agentic RAG chat route.
    LangGraph 版聊天 API
"""

from fastapi import APIRouter, HTTPException

from backend.schemas import AgentChatRequest, AgentChatResponse
from services.agent_qa_service import answer_question_with_graph


router = APIRouter(
    tags=["agent"],
)


@router.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat_with_document(request: AgentChatRequest) -> AgentChatResponse:
    """Answer a question using the LangGraph Agentic RAG workflow."""

    try:
        result = answer_question_with_graph(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AgentChatResponse(**result)
