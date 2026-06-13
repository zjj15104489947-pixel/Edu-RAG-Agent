"""管理 documents 表，存储文档管理信息
    SQLite document registry for uploaded and indexed course materials.
"""

from datetime import datetime
from pathlib import Path
import sqlite3

from core.config import get_settings

# 返回当前时间的字符串
def _now() -> str:
    """Return the current local time as a compact ISO string."""

    return datetime.now().isoformat(timespec="seconds")

# 读取 SQLite 数据库路径
def _get_db_path() -> Path:
    """Return the configured registry database path."""

    settings = get_settings()
    return Path(settings.document_registry_db)

# 打开 SQLite 数据库连接
def _connect() -> sqlite3.Connection:
    """Open a SQLite connection and return rows as dictionaries."""

    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True) # 确保数据库所在目录存在，如果没有自动创建

    connection = sqlite3.connect(db_path) # 打开 SQLite 数据库连接 
    connection.row_factory = sqlite3.Row # 让查询结果可按字段名访问，可转为字典
    return connection

# 把 SQLite 查询结果转成字典
def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a SQLite row to a plain dictionary."""

    if row is None:
        return None
    return dict(row)

# 创建 registry 表
def init_document_registry() -> None:
    """Create the document registry database and table if needed."""
    """ 文档唯一 ID，主键，不能重复
        原始文件名
        文件本地保存路径
        文件类型
        文件状态
        索引成功后生成 chunk 数
        创建时间
        更新时间
        如果失败，保存错误信息
        文件内容 hash，用于判断文件内容是否变化
        预留字段，用来管理同一教材不同格式
    """
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,      
                original_filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_message TEXT DEFAULT '',
                content_hash TEXT DEFAULT '',
                source_group_id TEXT DEFAULT ''
            )
            """
        )

# 创建或更新文档记录
def create_or_update_document_record(
    document_id: str,
    original_filename: str,
    stored_path: str,
    file_type: str,
    status: str = "uploaded",
    content_hash: str = "",
    source_group_id: str = "",
) -> None:
    """Create a document record or update its mutable fields."""

    init_document_registry()
    now = _now()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                original_filename,
                stored_path,
                file_type,
                status,
                chunk_count,
                created_at,
                updated_at,
                error_message,
                content_hash,
                source_group_id
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, '', ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                original_filename = excluded.original_filename,
                stored_path = excluded.stored_path,
                file_type = excluded.file_type,
                status = excluded.status,
                chunk_count = 0,
                updated_at = excluded.updated_at,
                error_message = '',
                content_hash = excluded.content_hash,
                source_group_id = excluded.source_group_id
            """,
            (
                document_id,
                original_filename,
                stored_path,
                file_type,
                status,
                now,
                now,
                content_hash,
                source_group_id,
            ),
        )

# 更新某个文档转态
def update_document_status(
    document_id: str,
    status: str,
    chunk_count: int | None = None,
    error_message: str = "",
) -> None:
    """Update status fields for one document record."""

    init_document_registry()
    now = _now()

    with _connect() as connection:
        if chunk_count is None:
            connection.execute(
                """
                UPDATE documents
                SET status = ?, updated_at = ?, error_message = ?
                WHERE document_id = ?
                """,
                (status, now, error_message, document_id),
            )
        else:
            connection.execute(
                """
                UPDATE documents
                SET status = ?, chunk_count = ?, updated_at = ?, error_message = ?
                WHERE document_id = ?
                """,
                (status, chunk_count, now, error_message, document_id),
            )

# 标记正在索引
def mark_indexing(document_id: str) -> None:
    """Mark a document as currently being indexed."""

    update_document_status(document_id, "indexing", error_message="")

# 索引成功后调用，把状态变成 indexed，并记录 chunk 数
def mark_indexed(document_id: str, chunk_count: int) -> None:
    """Mark a document as successfully indexed."""

    update_document_status(
        document_id,
        "indexed",
        chunk_count=chunk_count,
        error_message="",
    )

# 索引失败后调用，把状态变成 failed
def mark_failed(document_id: str, error_message: str) -> None:
    """Mark a document as failed and store the error message."""

    update_document_status(document_id, "failed", error_message=error_message)

# 查询 registry
def get_document(document_id: str) -> dict | None:
    """Return one document registry record by id."""

    init_document_registry()

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

    return _row_to_dict(row)

# 列出所有文档
def list_documents() -> list[dict]:
    """Return all document registry records, newest first."""

    init_document_registry()

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM documents
            ORDER BY updated_at DESC, created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]

# 从 SQLite registry 删除一条文档记录
def delete_document_record(document_id: str) -> bool:
    """Delete one document registry record by id."""

    init_document_registry()

    with _connect() as connection:
        cursor = connection.execute(
            """
            DELETE FROM documents
            WHERE document_id = ?
            """,
            (document_id,),
        )

    return cursor.rowcount > 0