""" Pydantic request and response schemas for the FastAPI backend.
    定义请求体和响应体结构
"""

from typing import Any

from pydantic import BaseModel

# 索引本地文件
class IndexLocalRequest(BaseModel):
    """Request body for indexing a local document path."""

    file_path: str
    chunk_size: int | None = None
    chunk_overlap: int | None = None

# 提问
class ChatRequest(BaseModel):
    """Request body for RAG question answering."""

    question: str
    document_id: str | None = None
    top_k: int | None = None

# 错误返回
class ErrorResponse(BaseModel):
    """Simple error response."""

    detail: str

# 文档操作返回
class DocumentResponse(BaseModel):
    """Generic document registry response."""

    document: dict[str, Any] | None

# 多个文档操作返回
class DocumentsResponse(BaseModel):
    """Document list response."""

    documents: list[dict[str, Any]]

# 问答返回
class ChatResponse(BaseModel):
    """RAG chat response."""

    question: str
    answer: str
    sources: list[dict[str, Any]]

# LangGraph 版提问
class AgentChatRequest(BaseModel):
    """Request body for LangGraph Agentic RAG question answering."""

    question: str
    document_id: str | None = None
    top_k: int | None = None

# LangGraph 版问答返回
class AgentChatResponse(BaseModel):
    """Response body for LangGraph Agentic RAG question answering."""

    question: str
    rewritten_query: str
    answer: str
    sources: list[dict[str, Any]]
    evidence_status: str
    evidence_reason: str
    grounding_status: str
    grounding_reason: str
    document_id: str | None = None
    top_k: int

# 上传文件返回
class UploadDocumentResponse(BaseModel):
    """Response body for uploaded document files."""

    document_id: str
    original_filename: str
    stored_path: str
    file_type: str
    status: str
    content_hash: str
    message: str

# 索引某个文档
class IndexDocumentRequest(BaseModel):
    """Request body for indexing a registered document."""

    chunk_size: int | None = None
    chunk_overlap: int | None = None

# 删除文档返回
class DeleteDocumentResponse(BaseModel):
    """Response body for deleting a document."""

    document_id: str
    deleted_chunks: int
    registry_deleted: bool
    file_deleted: bool
    message: str
