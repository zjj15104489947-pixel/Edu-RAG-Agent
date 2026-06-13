"""Command-line script for asking questions over indexed course materials."""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.qa_service import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a question based on indexed course materials."
    )
    parser.add_argument("question", help="User question.")
    parser.add_argument(
        "--document-id",
        default=None,
        help="Optional document_id filter. If omitted, search all indexed documents.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve.",
    )
    args = parser.parse_args()

    result = answer_question(
        question=args.question,
        document_id=args.document_id,
        top_k=args.top_k,
    )

    print("\n" + "=" * 80)
    print("问题：")
    print(result.get("question", args.question))

    print("\n" + "=" * 80)
    print("回答：")
    print(result.get("answer", ""))

    print("\n" + "=" * 80)
    print("来源：")
    pprint(result.get("sources", []))


if __name__ == "__main__":
    main()