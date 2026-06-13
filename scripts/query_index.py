""" 命令行脚本，从Chroma中检索
    Command-line script for querying the Chroma vector index.
"""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import get_settings
from rag.vector_store import get_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the Chroma vector index.")
    parser.add_argument("query", help="User query.")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--document-id", default=None, help="Filter by document_id.")
    args = parser.parse_args()

    settings = get_settings()
    top_k = args.top_k or settings.retrieval_top_k

    vector_store = get_vector_store()

    search_filter = None
    if args.document_id:
        search_filter = {"document_id": args.document_id}

    print(f"查询: {args.query}")
    print(f"Top K: {top_k}")
    print(f"Filter: {search_filter}")
    print("正在检索...")

    results = vector_store.similarity_search(
        args.query,
        k=top_k,
        filter=search_filter,
    )

    print(f"\n检索到 {len(results)} 个结果:\n")

    for index, doc in enumerate(results, start=1):
        print("=" * 80)
        print(f"结果 {index}")
        print(f"metadata: {doc.metadata}")
        print("-" * 80)
        preview = doc.page_content[:800].replace("\n", " ")
        print(preview)


if __name__ == "__main__":
    main()