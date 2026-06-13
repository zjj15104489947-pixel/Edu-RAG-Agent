"""命令行脚本：在构建索引前检查 PDF 页数、文本层和 OCR 需求。"""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from loaders.pdf_loader import inspect_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a PDF file.")
    parser.add_argument("pdf_path", help="Path to the PDF file.")
    args = parser.parse_args()

    try:
        result = inspect_pdf(args.pdf_path)
        pprint(result)
    except Exception as exc:
        print(f"检查 PDF 失败：{exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
