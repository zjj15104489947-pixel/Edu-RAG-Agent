""" Chat-related FastAPI routes.
    普通聊天 API
"""

from fastapi import APIRouter, HTTPException

from backend.schemas import ChatRequest, ChatResponse
from services.qa_service import answer_question


router = APIRouter(
    tags=["chat"],
)

# POST /chat
@router.post("/chat", response_model=ChatResponse)
def chat_with_document(request: ChatRequest) -> ChatResponse:
    """Answer a question using indexed course materials."""

    try:
        result = answer_question(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
    )