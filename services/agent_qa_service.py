""" Service layer for LangGraph Agentic RAG question answering.
    LangGraph 编排的问答
"""

from functools import lru_cache

from core.config import get_settings
from graphs.edu_qa_graph import build_edu_qa_graph


@lru_cache
def get_edu_qa_graph():
    """Return the cached compiled EduRAG QA graph."""

    return build_edu_qa_graph()


def answer_question_with_graph(
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
) -> dict:
    """Answer a question with the LangGraph Agentic RAG workflow."""

    settings = get_settings()
    actual_top_k = top_k or settings.retrieval_top_k

    initial_state = {
        "question": question,
        "document_id": document_id,
        "top_k": actual_top_k,
        "rewritten_query": "",
        "retrieved_docs": [],
        "context": "",
        "sources": [],
        "evidence_status": "",
        "evidence_reason": "",
        "answer": "",
        "grounding_status": "",
        "grounding_reason": "",
    }

    graph = get_edu_qa_graph()
    final_state = graph.invoke(initial_state)

    return {
        "question": question,
        "rewritten_query": final_state.get("rewritten_query", ""),
        "answer": final_state.get("answer", ""),
        "sources": final_state.get("sources", []),
        "evidence_status": final_state.get("evidence_status", ""),
        "evidence_reason": final_state.get("evidence_reason", ""),
        "grounding_status": final_state.get("grounding_status", ""),
        "grounding_reason": final_state.get("grounding_reason", ""),
        "document_id": document_id,
        "top_k": actual_top_k,
    }
