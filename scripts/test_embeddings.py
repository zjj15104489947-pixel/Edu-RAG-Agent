"""命令行脚本，用来测试 embedding 是否可用"""

"""Command-line script for testing the local embedding model."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag.embeddings import get_embedding_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the embedding model.")
    parser.add_argument(
        "text",
        nargs="?",
        default="What is packet switching?",
        help="Text to embed.",
    )
    args = parser.parse_args()

    embedding_model = get_embedding_model()

    vector = embedding_model.embed_query(args.text)

    print(f"输入文本: {args.text}")
    print(f"向量类型: {type(vector)}")
    print(f"向量维度: {len(vector)}")
    print(f"前 5 个数: {vector[:5]}")


if __name__ == "__main__":
    main()