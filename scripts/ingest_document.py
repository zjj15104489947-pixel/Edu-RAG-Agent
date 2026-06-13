"""命令行脚本，把文件变成向量存入Chroma
    Command-line script for ingesting PDF or Markdown documents into Chroma.
"""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.document_indexing_service import index_document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index a PDF or Markdown document into Chroma."
    )
    parser.add_argument("file_path", help="Path to a PDF or Markdown file.")
    parser.add_argument("--chunk-size", type=int, default=None)
    parser.add_argument("--chunk-overlap", type=int, default=None)
    args = parser.parse_args()

    try:
        result = index_document(
            file_path=args.file_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except Exception as exc:
        print(f"索引失败: {exc}")
        raise SystemExit(1) from exc

    pprint(result)


if __name__ == "__main__":
    main()
