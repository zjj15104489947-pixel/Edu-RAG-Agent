""" Document lifecycle management service.
    上传文件管理
"""

from pathlib import Path

from core.config import get_settings
from services.document_indexing_service import delete_document_index
from services.document_registry_service import (
    delete_document_record,
    get_document,
)


# 判断是否在 uploads 文件夹里
def _is_path_inside(child_path: Path, parent_path: Path) -> bool:
    """Return whether child_path is inside parent_path after resolving paths."""

    try:
        child_path.resolve().relative_to(parent_path.resolve())
        return True
    except ValueError:
        return False


# 删除文件及相关数据
def delete_document(document_id: str) -> dict:
    """Delete a document from Chroma, registry, and uploaded file storage."""

    document = get_document(document_id)

    if document is None:
        raise ValueError("Document not found.")

    stored_path_value = document.get("stored_path")
    settings = get_settings()
    upload_dir = Path(settings.document_upload_dir)

    deleted_chunks = delete_document_index(document_id)

    file_deleted = False
    if stored_path_value:
        stored_path = Path(stored_path_value)

        if _is_path_inside(stored_path, upload_dir) and stored_path.exists():
            stored_path.unlink()
            file_deleted = True

    registry_deleted = delete_document_record(document_id)

    return {
        "document_id": document_id,
        "deleted_chunks": deleted_chunks,
        "registry_deleted": registry_deleted,
        "file_deleted": file_deleted,
        "message": "Document deleted successfully.",
    }