#!/usr/bin/env python3
"""将 data/ 下的 JSON 同步进 index.html，便于 file:// 直接打开单文件。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    html_path = root / "index.html"
    html = html_path.read_text(encoding="utf-8")

    days = json.loads((root / "data/days.json").read_text(encoding="utf-8"))
    locations = json.loads((root / "data/locations.json").read_text(encoding="utf-8"))
    map_cfg = json.loads((root / "data/map.json").read_text(encoding="utf-8"))
    payload = {"days": days, "locations": locations, "map": map_cfg}
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    embedded = embedded.replace("</", "<\\/")

    embed_block = (
        '    <script id="travel-embedded-data" type="application/json">\n'
        f"{embedded}\n"
        "    </script>\n"
    )

    if 'id="travel-embedded-data"' not in html:
        marker = '    <div id="app"></div>\n    <script>'
        if marker not in html:
            print("index.html 结构异常，找不到插入点。", file=sys.stderr)
            return 1
        html = html.replace(marker, f'    <div id="app"></div>\n{embed_block}    <script>', 1)
    else:
        html = re.sub(
            r'\s*<script id="travel-embedded-data" type="application/json">[\s\S]*?</script>\s*',
            "\n" + embed_block,
            html,
            count=1,
        )

    html_path.write_text(html, encoding="utf-8")
    print(f"已同步到 {html_path}（内嵌约 {len(embedded)} 字节）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
