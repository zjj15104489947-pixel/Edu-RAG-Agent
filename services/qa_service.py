""" 基于 Deepseek 的 RAG 问答服务
    Question answering service built on retrieval and DeepSeek generation.
"""

from langchain_core.documents import Document

from core.config import get_settings
from core.llm import get_chat_model
from rag.prompts import RAG_QA_PROMPT
from rag.vector_store import get_vector_store

# 基于提问检索相应 chunks
def retrieve_relevant_chunks(
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
) -> list[Document]:
    """Retrieve relevant chunks from Chroma for a user question."""

    settings = get_settings()
    actual_top_k = top_k or settings.retrieval_top_k
    vector_store = get_vector_store()

    # 如果指定 document_id ，在特定教材检索，否则在全库检索
    search_filter = None
    if document_id:
        search_filter = {"document_id": document_id}

    return vector_store.similarity_search(
        question,
        k=actual_top_k,
        filter=search_filter
    )

# 为用户显示答案来源
def format_source(doc: Document) -> str:
    """Format a document source for display."""
    
    metadata = doc.metadata
    source = metadata.get("source","unknown")

    if metadata.get("file_type") == "pdf":
        page = metadata.get("page","unknown")
        return f"{source}, 第 {page} 页"
    
    if metadata.get("file_type") == "markdown":
        header_path = metadata.get("header_path","unknown section")
        return f"{source}, 章节：{header_path}"
    
    return source

# 包装 chunks 后序会放入 RAG_QA_PROMPT 的 {context}
def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into a prompt context string."""

    context_parts = []
    for index,doc in enumerate(docs,start = 1):
        source = format_source(doc)
        context_parts.append(
            f"[片段 {index} | 来源：{source}]\n{doc.page_content}"
        )

    return "\n\n".join(context_parts)

# 生成给前端或日志用的结构化数据
def build_sources(docs: list[Document]) -> list[dict]:
    """Build structured source metadata from retrieved documents."""

    sources = []

    for doc in docs:
        metadata = doc.metadata
        sources.append(
            {
                "document_id": metadata.get("document_id"),
                "source": metadata.get("source"),
                "file_type": metadata.get("file_type"),
                "page": metadata.get("page"),
                "section_title": metadata.get("section_title"),
                "header_path": metadata.get("header_path"),
                "chunk_index": metadata.get("chunk_index"),
            }
        )

    return sources

# 回答问题主函数
def answer_question(
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
) -> dict:
    """Answer a user question using retrieved course material chunks."""

    docs = retrieve_relevant_chunks(
        question=question,
        document_id=document_id,
        top_k=top_k,
    )

    if not docs:
        return {
            "question": question,
            "answer": "当前资料不足以回答该问题。",
            "sources": [],
        }

    context = format_context(docs)

    llm = get_chat_model()
    messages = RAG_QA_PROMPT.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    response = llm.invoke(messages)

    return {
        "question": question,
        "answer": response.content,
        "sources": build_sources(docs),
    }