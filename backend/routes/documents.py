""" Document-related FastAPI routes.
    负责文档相关 API
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.schemas import (
    DocumentResponse,
    DocumentsResponse,
    IndexDocumentRequest,
    IndexLocalRequest,
    UploadDocumentResponse,
    DeleteDocumentResponse,
)
from services.document_indexing_service import index_document
from services.document_registry_service import get_document, list_documents
from services.document_storage_service import save_uploaded_document
from services.document_management_service import delete_document


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# GET /documents 获取文档列表
@router.get("", response_model=DocumentsResponse)
def get_documents() -> DocumentsResponse:
    """List all registered documents."""

    documents = list_documents()
    return DocumentsResponse(documents=documents)


# GET /documents/{document_id} 获取单个文档
@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_by_id(document_id: str) -> DocumentResponse:
    """Get one document registry record."""

    document = get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentResponse(document=document)


# POST /documents/upload 上传文件
@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadDocumentResponse:
    """Upload a PDF or Markdown document and register it as uploaded."""

    try:
        file_bytes = await file.read()
        result = save_uploaded_document(
            filename=file.filename or "",
            file_bytes=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await file.close()

    return UploadDocumentResponse(**result)


# POST /documents/{document_id}/index 索引上传的文件
@router.post("/{document_id}/index")
def index_registered_document(
    document_id: str,
    request: IndexDocumentRequest,
) -> dict:
    """Index an uploaded document by document_id."""

    document = get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    stored_path = document.get("stored_path")

    if not stored_path:
        raise HTTPException(status_code=400, detail="Document has no stored path.")

    try:
        return index_document(
            file_path=stored_path,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            document_id=document_id,
            original_filename=document.get("original_filename") or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    

# POST /documents/index-local 索引本地文件
@router.post("/index-local")
def index_local_document(request: IndexLocalRequest) -> dict:
    """Index a local PDF or Markdown file path."""

    try:
        return index_document(
            file_path=request.file_path,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    

# DELETE /documents/{document_id}
@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document_by_id(document_id: str) -> DeleteDocumentResponse:
    """Delete one document, its vector chunks, and uploaded file if applicable."""

    try:
        result = delete_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DeleteDocumentResponse(**result)
