#!/usr/bin/env python3
"""
Learning Agent MVP v0.1 — CLI 入口

Usage:
    python run.py --chapter data/chapter1.txt
    python run.py --chapter data/chapter1.txt --output output
"""

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.runner import Runner


def main():
    parser = argparse.ArgumentParser(description="Learning Agent MVP v0.1")
    parser.add_argument(
        "--chapter",
        required=True,
        help="教材章节文件路径（.txt, UTF-8）",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="输出目录（默认: output）",
    )
    args = parser.parse_args()

    chapter_path = Path(args.chapter)
    if not chapter_path.exists():
        print(f"错误：文件不存在: {args.chapter}")
        sys.exit(1)

    runner = Runner(output_base=args.output)
    report_path = runner.run(str(chapter_path))

    print(f"\nDone. Report: {report_path}")


if __name__ == "__main__":
    main()
