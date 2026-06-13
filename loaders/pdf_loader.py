"""PDF 资料读取工具，负责提取页级文本并判断 PDF 是否具有可提取文本层。"""

from pathlib import Path

import fitz


def _validate_pdf_path(pdf_path: str) -> Path:
    """Validate PDF path and return a Path object."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {pdf_path}")

    if path.is_dir():
        raise IsADirectoryError(f"路径是一个目录，不是文件: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"文件不是 PDF 格式: {pdf_path}")

    return path


def load_pdf_pages(pdf_path: str) -> list[dict]:
    """Load a PDF and return one dictionary per page."""

    path = _validate_pdf_path(pdf_path)
    pages = []

    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            pages.append(
                {
                    "page": index,
                    "text": page.get_text(),
                    "source": path.name,
                }
            )

    return pages


def inspect_pdf(pdf_path: str, preview_pages: int = 3) -> dict:
    """Inspect a PDF and return basic page/text metadata."""

    path = _validate_pdf_path(pdf_path)
    preview = []
    sampled_lengths = []

    with fitz.open(path) as document:
        page_count = document.page_count
        pages_to_preview = min(preview_pages, page_count)

        for index in range(pages_to_preview):
            page = document.load_page(index)
            text = page.get_text()
            stripped_text = text.strip()
            sampled_lengths.append(len(stripped_text))
            preview.append(
                {
                    "page": index + 1,
                    "text_length": len(text),
                    "text_preview": stripped_text[:1000],
                }
            )

    average_text_length = (
        sum(sampled_lengths) / len(sampled_lengths) if sampled_lengths else 0
    )
    is_scanned = average_text_length < 50

    return {
        "file_path": str(path),
        "file_name": path.name,
        "page_count": page_count,
        "preview": preview,
        "pdf_type": "scanned_pdf" if is_scanned else "text_pdf",
        "need_ocr": is_scanned,
    }
