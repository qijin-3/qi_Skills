#!/usr/bin/env python3
"""打印/创建当日日报输出路径，供任意宿主（Cursor / OpenClaw / 脚本）调用。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ensure_layout, layout, resolve_digest_root, today_str  # noqa: E402


def main() -> None:
    """CLI：解析并可选创建输出目录。"""
    parser = argparse.ArgumentParser(description="解析 daily-news-digest 输出路径")
    parser.add_argument("--date", default="", help="YYYY-MM-DD，默认今天")
    parser.add_argument("--root", default="", help="覆盖日报根目录")
    parser.add_argument("--mkdir", action="store_true", help="创建 day/raw/sections")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    date_str = args.date or today_str()
    root = resolve_digest_root(args.root or None)
    paths = ensure_layout(root, date_str) if args.mkdir else layout(root, date_str)
    payload = {k: str(v) for k, v in paths.items()}
    payload["date"] = date_str

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"DIGEST_ROOT={payload['root']}")
    print(f"DIGEST_DAY={payload['day']}")
    print(f"DIGEST_RAW={payload['raw']}")
    print(f"DIGEST_SECTIONS={payload['sections']}")
    print(f"DIGEST_INDEX={payload['index']}")
    print(f"DIGEST_DATE={date_str}")


if __name__ == "__main__":
    main()
