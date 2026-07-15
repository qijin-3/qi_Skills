#!/usr/bin/env python3
"""把模板与各板块 fragment / 健康报告拼成最终 index.html。"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any


def skill_root() -> Path:
    """返回技能根目录。"""
    return Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    """读取 UTF-8 文本；缺失则返回空字符串。"""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def escape_html(s: str) -> str:
    """转义 HTML 文本节点。"""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def source_rows_html(sources: list[dict[str, Any]]) -> str:
    """渲染一组订阅源表格行。"""
    rows: list[str] = []
    for src in sources:
        status = src.get("status", "?")
        badge = {"ok": "ok", "empty": "empty", "fail": "fail"}.get(status, status)
        rows.append(
            "<tr>"
            f"<td>{escape_html(src.get('name') or src.get('id') or '')}</td>"
            f"<td><span class='badge badge-{badge}'>{escape_html(status)}</span></td>"
            f"<td>{src.get('item_count', 0)}</td>"
            f"<td class='mono'>{escape_html(src.get('latest_pub_date') or '—')}</td>"
            f"<td class='mono small'>{escape_html(src.get('url_used') or '—')}</td>"
            f"<td class='small'>{escape_html(src.get('error') or '')}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='6'>无来源</td></tr>")
    return "\n".join(rows)


def table_html(tbody: str) -> str:
    """包装健康表。"""
    return f"""
<table class="health-table">
  <thead>
    <tr>
      <th>来源</th><th>状态</th><th>条数</th>
      <th>最新时间</th><th>使用 URL</th><th>错误</th>
    </tr>
  </thead>
  <tbody>
{tbody}
  </tbody>
</table>
""".strip()


def build_health_grouped(raw_dir: Path) -> str:
    """按板块分组生成可折叠健康报告（默认收起，summary 只看总结）。"""
    blocks: list[str] = []
    groups = [
        ("x-ai", "X-AI 日报", False),
        ("design", "设计日报", True),
        ("news", "今日新闻", False),
    ]
    for section_id, label, by_domain in groups:
        path = raw_dir / f"{section_id}.json"
        if not path.exists():
            blocks.append(
                f'<details class="health-group">'
                f"<summary><span class='health-summary-title'>{escape_html(label)}</span>"
                f"<span class='health-summary-line'>缺少 {escape_html(section_id)}.json</span></summary>"
                f"</details>"
            )
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = data.get("summary") or {}
        health_line = summary.get("health_line") or ""
        sources = data.get("sources") or []

        summary_block = (
            f"<summary>"
            f"<div class='health-summary-main'>"
            f"<span class='health-summary-title'>{escape_html(label)}</span>"
            f"<span class='health-summary-line'>{escape_html(health_line)}</span>"
            f"</div>"
            f"<div class='kpi-row summary-kpi'>"
            f"<span class='kpi'><b>{summary.get('sources_ok', 0)}</b>成功</span>"
            f"<span class='kpi'><b>{summary.get('sources_fail', 0)}</b>失败</span>"
            f"<span class='kpi'><b>{summary.get('sources_empty', 0)}</b>空窗</span>"
            f"<span class='kpi'><b>{summary.get('items_total', 0)}</b>条目</span>"
            f"</div>"
            f"<span class='health-chevron' aria-hidden='true'></span>"
            f"</summary>"
        )

        body_parts: list[str] = ['<div class="health-body">']
        if by_domain:
            domains: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
            for src in sources:
                domains.setdefault(src.get("domain") or "其他", []).append(src)
            if len(domains) > 1:
                for dom, dom_sources in domains.items():
                    body_parts.append(
                        f"<h3 class='health-sub'>{escape_html(dom)}</h3>"
                    )
                    body_parts.append(table_html(source_rows_html(dom_sources)))
            else:
                body_parts.append(table_html(source_rows_html(sources)))
        else:
            body_parts.append(table_html(source_rows_html(sources)))
        body_parts.append("</div>")

        blocks.append(
            f'<details class="health-group">{summary_block}{"".join(body_parts)}</details>'
        )

    return "\n".join(blocks) if blocks else "<p class='empty-note'>暂无健康数据</p>"


def load_meta(sections_dir: Path, section_id: str) -> dict[str, Any]:
    """读取板块 meta.json；缺失时给默认空摘要。"""
    path = sections_dir / f"{section_id}.meta.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "section": section_id,
        "health_line": "（缺少健康摘要）",
        "sources_ok": 0,
        "sources_fail": 0,
        "items_total": 0,
    }


def compose(out_dir: Path, date_str: str) -> Path:
    """组装最终 HTML，写入 out_dir/index.html。"""
    template = (skill_root() / "assets" / "template.html").read_text(encoding="utf-8")
    sections_dir = out_dir / "sections"
    raw_dir = out_dir / "raw"

    fragments = {
        "aihot": read_text(sections_dir / "aihot.fragment.html"),
        "x-ai": read_text(sections_dir / "x-ai.fragment.html"),
        "design": read_text(sections_dir / "design.fragment.html"),
        "news": read_text(sections_dir / "news.fragment.html"),
    }
    metas = {sid: load_meta(sections_dir, sid) for sid in fragments}

    health_html = build_health_grouped(raw_dir)

    html = template
    html = html.replace("{{DATE}}", escape_html(date_str))
    html = html.replace(
        "{{GENERATED_AT}}",
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    html = html.replace("{{FRAGMENT_AIHOT}}", fragments["aihot"])
    html = html.replace("{{FRAGMENT_X_AI}}", fragments["x-ai"])
    html = html.replace("{{FRAGMENT_DESIGN}}", fragments["design"])
    html = html.replace("{{FRAGMENT_NEWS}}", fragments["news"])
    html = html.replace(
        "{{HEALTH_LINE_AIHOT}}", escape_html(metas["aihot"].get("health_line", ""))
    )
    html = html.replace(
        "{{HEALTH_LINE_X_AI}}", escape_html(metas["x-ai"].get("health_line", ""))
    )
    html = html.replace(
        "{{HEALTH_LINE_DESIGN}}", escape_html(metas["design"].get("health_line", ""))
    )
    html = html.replace(
        "{{HEALTH_LINE_NEWS}}", escape_html(metas["news"].get("health_line", ""))
    )
    html = html.replace("{{HEALTH_TABLE}}", health_html)

    html = re.sub(r"\{\{[A-Z0-9_]+\}\}", "", html)

    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> None:
    """CLI：组装资讯日报 HTML。"""
    parser = argparse.ArgumentParser(description="组装资讯日报 HTML")
    parser.add_argument("--out", type=Path, required=True, help="当日输出目录")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    path = compose(args.out, args.date)
    print(path)


if __name__ == "__main__":
    main()
