"""Markdown 资料读取工具，负责加载 Markdown 文本并检查文件基本信息。"""

from pathlib import Path


def load_markdown_text(md_path: str) -> str:
    """Load a Markdown file as plain text."""

    path = Path(md_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {md_path}")
    if path.is_dir():
        raise IsADirectoryError(f"路径是一个目录，不是文件: {md_path}")
    if path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"文件不是Markdown格式: {md_path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"无法解码文件，可能不是UTF-8编码: {md_path}") from exc


def inspect_markdown(md_path: str) -> dict:
    """Inspect a Markdown file and return basic metadata."""

    path = Path(md_path)
    text = load_markdown_text(md_path)

    return {
        "file_path": str(path),
        "file_name": path.name,
        "char_count": len(text),
        "text_preview": text[:1000],
    }
