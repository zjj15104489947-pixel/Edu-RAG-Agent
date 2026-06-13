"""命令行脚本：在构建索引前检查 Markdown 文件能否正常读取。"""

import argparse
from pathlib import Path
import sys

from rich.pretty import pprint

# 得到项目根目录并添加到 sys.path，以便导入 loaders 模块
PROJECT_ROOT = Path(__file__).resolve().parents[1] 
sys.path.insert(0, str(PROJECT_ROOT))

from loaders.markdown_loader import inspect_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a Markdown file.")
    parser.add_argument("md_path", help="Path to the Markdown file.")
    args = parser.parse_args()

    try:
        result = inspect_markdown(args.md_path)
        pprint(result)
    except Exception as exc:
        print(f"检查 Markdown 失败：{exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
