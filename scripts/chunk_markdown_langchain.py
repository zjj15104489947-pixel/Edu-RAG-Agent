"""langchain封装版命令行脚本：读取 Markdown 文本并切分成 RAG 使用的 chunk。"""
import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from loaders.markdown_loader import load_markdown_text
from rag.langchain_chunker import chunk_markdown_text_with_langchain


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk a Markdown file with LangChain.")
    parser.add_argument("md_path", help="Path to the Markdown file.")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    args = parser.parse_args()

    md_path = Path(args.md_path)
    markdown_text = load_markdown_text(str(md_path))

    chunks = chunk_markdown_text_with_langchain(
        markdown_text=markdown_text,
        source=md_path.name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print(f"Markdown 字符数: {len(markdown_text)}")
    print(f"Chunk 数量: {len(chunks)}")
    print("前 3 个 chunk 预览:")
    pprint(chunks[:3])


if __name__ == "__main__":
    main()