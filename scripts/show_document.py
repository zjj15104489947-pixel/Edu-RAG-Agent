""" 根据 document_id 查询一条文档记录
    Command-line script for showing one document registry record.
"""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.document_registry_service import get_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Show one document registry record.")
    parser.add_argument("document_id", help="Document id to look up.")
    args = parser.parse_args()

    document = get_document(args.document_id)
    pprint(document)


if __name__ == "__main__":
    main()
