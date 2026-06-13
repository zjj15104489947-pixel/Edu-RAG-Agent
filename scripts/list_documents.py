""" 列出 SQLite registry 里所有文档记录
    Command-line script for listing document registry records.
"""

from pathlib import Path
import sys

from rich.pretty import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.document_registry_service import list_documents


def main() -> None:
    documents = list_documents()
    pprint(documents)


if __name__ == "__main__":
    main()
