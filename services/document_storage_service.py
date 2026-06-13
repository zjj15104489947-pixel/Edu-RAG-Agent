""" Document storage service for saving uploaded course-material files.
    负责保存上传文件
"""

import re
from hashlib import sha1
from pathlib import Path

from core.config import get_settings
from services.document_registry_service import create_or_update_document_record


SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".md", ".markdown"}

# 安全处理文件名
def _sanitize_filename(filename: str) -> str:
    """Return a safe filename without directory components."""

    name = Path(filename).name.strip()
    name = name.replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)

# 把后缀转化成系统内部类型
def _get_file_type_from_suffix(suffix: str) -> str:
    """Return file type name from a supported file suffix."""

    if suffix == ".pdf":
        return "pdf"
    if suffix in {".md", ".markdown"}:
        return "markdown"

    raise ValueError(
        f"Unsupported file type: {suffix}. "
        f"Supported types: {sorted(SUPPORTED_UPLOAD_EXTENSIONS)}"
    )

# 根据文件名和内容 hash 生成 document_id
def _make_document_id(safe_filename: str, content_hash: str) -> str:
    """Create a stable document id from a filename and content hash."""

    stem = Path(safe_filename).stem
    safe_stem = stem.replace(" ", "_")
    return f"{safe_stem}_{content_hash[:12]}"

# 保存上传的文件
def save_uploaded_document(filename: str, file_bytes: bytes) -> dict:
    """Save an uploaded document file and create an uploaded registry record."""

    if not filename:
        raise ValueError("Uploaded file must have a filename.")

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    safe_filename = _sanitize_filename(filename)
    suffix = Path(safe_filename).suffix.lower()

    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported types: {sorted(SUPPORTED_UPLOAD_EXTENSIONS)}"
        )

    file_type = _get_file_type_from_suffix(suffix)
    content_hash = sha1(file_bytes).hexdigest()
    document_id = _make_document_id(safe_filename, content_hash)

    settings = get_settings()
    upload_dir = Path(settings.document_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{document_id}{suffix}"
    stored_path = upload_dir / stored_filename
    stored_path.write_bytes(file_bytes)

    create_or_update_document_record(
        document_id=document_id,
        original_filename=safe_filename,
        stored_path=str(stored_path),
        file_type=file_type,
        status="uploaded",
        content_hash=content_hash,
    )

    return {
        "document_id": document_id,
        "original_filename": safe_filename,
        "stored_path": str(stored_path),
        "file_type": file_type,
        "status": "uploaded",
        "content_hash": content_hash,
        "message": "Document uploaded successfully.",
    }