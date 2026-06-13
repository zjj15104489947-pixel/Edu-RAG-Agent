"""langchain封装版命令行脚本：读取 PDF 页级文本并切分成 RAG 使用的 chunk。"""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from loaders.pdf_loader import load_pdf_pages
from rag.langchain_chunker import chunk_pdf_pages_with_langchain


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk a PDF file.")
    parser.add_argument("pdf_path", help="Path to the PDF file.")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    args = parser.parse_args()

    pages = load_pdf_pages(args.pdf_path)
    chunks = chunk_pdf_pages_with_langchain(
        pages,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print(f"PDF 页数: {len(pages)}")
    print(f"Chunk 数量: {len(chunks)}")
    print("前 3 个 chunk 预览:")
    pprint(chunks[:3])


if __name__ == "__main__":
    main()