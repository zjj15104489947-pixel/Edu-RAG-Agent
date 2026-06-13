"""Document indexing service for loading, chunking, and storing course materials.

给定一个 PDF / Markdown 文件路径，本模块负责完成：
读取文件 → 切分 chunk → 删除旧索引 → 写入 Chroma → 更新文档 registry。
"""

from hashlib import sha1
from pathlib import Path

from langchain_core.documents import Document

from core.config import get_settings
from loaders.markdown_loader import load_markdown_text
from loaders.pdf_loader import load_pdf_pages
from rag.langchain_chunker import (
    chunk_markdown_text_with_langchain,
    chunk_pdf_pages_with_langchain,
)
from rag.vector_store import get_vector_store
from services.document_registry_service import (
    create_or_update_document_record,
    mark_failed,
    mark_indexed,
    update_document_status,
)


SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown"}

# 把文件后缀变成系统内部的 file_type
def _get_file_type(file_path: str) -> str:
    """Return the supported file type name for a document path."""

    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return "pdf"
    if suffix in {".md", ".markdown"}:
        return "markdown"

    raise ValueError(
        f"暂不支持该文件类型: {suffix}，当前支持: {sorted(SUPPORTED_EXTENSIONS)}"
    )

# 生成文件内容 hash
def make_content_hash(file_path: str) -> str:
    """Create a SHA-1 content hash for a document file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    if path.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件: {file_path}")

    return sha1(path.read_bytes()).hexdigest()

# 生成文档ID
def make_document_id(file_path: str) -> str:
    """Create a stable document id from file content."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    if path.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件: {file_path}")

    digest = make_content_hash(str(path))[:12]

    safe_stem = path.stem.replace(" ", "_")

    return f"{safe_stem}_{digest}"


# 加载文件，判断类型，切chunk，补充metadata内容，返回document_id和chunks
def load_and_chunk_document(
    file_path: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    document_id: str | None = None,
) -> tuple[str, list[Document]]:
    """Load a supported document file and split it into LangChain chunks."""

    settings = get_settings()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    if path.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"暂不支持该文件类型: {suffix}，当前支持: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    actual_chunk_size = chunk_size or settings.chunk_size
    actual_chunk_overlap = chunk_overlap or settings.chunk_overlap

    actual_document_id = document_id or make_document_id(str(path))

    if suffix == ".pdf":
        pages = load_pdf_pages(str(path))
        chunks = chunk_pdf_pages_with_langchain(
            pages,
            chunk_size=actual_chunk_size,
            chunk_overlap=actual_chunk_overlap,
        )
        file_type = "pdf"

    elif suffix in {".md", ".markdown"}:
        markdown_text = load_markdown_text(str(path))
        chunks = chunk_markdown_text_with_langchain(
            markdown_text=markdown_text,
            source=path.name,
            chunk_size=actual_chunk_size,
            chunk_overlap=actual_chunk_overlap,
        )
        file_type = "markdown"

    else:
        raise ValueError(f"暂不支持该文件类型: {suffix}")

    for index, chunk in enumerate(chunks, start=1):
        chunk.metadata.update(
            {
                "document_id": actual_document_id,
                "source": path.name,
                "source_path": str(path),
                "file_type": file_type,
                "chunk_index": index,
            }
        )

    return actual_document_id, chunks


# 登记 registry，拿到chunks，删除旧索引，写入Chroma，更新 registry，返回索引报告
def index_document(
    file_path: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    document_id: str | None = None,
    original_filename: str | None = None,
) -> dict:
    """Index a PDF or Markdown file into the Chroma vector store."""

    path = Path(file_path)
    actual_document_id = document_id or make_document_id(str(path))
    file_type = _get_file_type(str(path))
    content_hash = make_content_hash(str(path))

    create_or_update_document_record(
        document_id=actual_document_id,
        original_filename=original_filename or path.name,
        stored_path=str(path),
        file_type=file_type,
        status="indexing",
        content_hash=content_hash,
    )

    try:
        actual_document_id, chunks = load_and_chunk_document(
            file_path=file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            document_id=actual_document_id,
        )

        deleted_count = delete_document_index(actual_document_id)

        if not chunks:
            update_document_status(
                document_id=actual_document_id,
                status="empty",
                chunk_count=0,
                error_message="No chunks were generated. Nothing was written to the vector store.",
            )
            return {
                "document_id": actual_document_id,
                "chunk_count": 0,
                "status": "empty",
                "message": "No chunks were generated. Nothing was written to the vector store.",
                "deleted_old_chunks": deleted_count,
            }

        vector_store = get_vector_store()

        ids = [
            f"{actual_document_id}_chunk_{index:05d}"
            for index in range(1, len(chunks) + 1)
        ]

        vector_store.add_documents(
            documents=chunks,
            ids=ids,
        )

        mark_indexed(actual_document_id, len(chunks))

        return {
            "document_id": actual_document_id,
            "chunk_count": len(chunks),
            "status": "indexed",
            "message": "Document index built successfully.",
            "deleted_old_chunks": deleted_count,
        }

    except Exception as exc:
        mark_failed(actual_document_id, str(exc))
        raise

# 删除 Chroma 中某个文档的旧 chunks
def delete_document_index(document_id: str) -> int:
    """Delete all Chroma chunks that belong to one document_id."""

    vector_store = get_vector_store()

    try:
        existing = vector_store.get(where={"document_id": document_id})
    except (AttributeError, TypeError):
        # Fallback for Chroma wrappers without a public get(where=...) method.
        # This uses Chroma's lower-level collection API directly.
        existing = vector_store._collection.get(where={"document_id": document_id})

    ids = existing.get("ids", [])

    if not ids:
        return 0

    vector_store.delete(ids=ids)

    return len(ids)
