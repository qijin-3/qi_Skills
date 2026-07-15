#!/usr/bin/env python3
"""从 aihot.json（feed.xml）按分类渲染 AIHOT fragment。无需浏览器。"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# 常见分类优先排序；未列出的按字母排在后面
CATEGORY_ORDER = [
    "AI 模型",
    "AI 产品",
    "行业动态",
    "论文",
    "技巧观点",
]


def escape(s: str) -> str:
    """转义 HTML。"""
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_date(iso_or_date: str) -> str:
    """ISO / YYYY-MM-DD → DD/MM/YYYY。"""
    d = (iso_or_date or "")[:10]
    if len(d) == 10 and d[4] == "-":
        y, m, day = d.split("-")
        return f"{day}/{m}/{y}"
    return d or ""


def clean_summary(raw: str) -> str:
    """去掉 feed 尾部的「阅读原文 / via AI HOT」装饰行。"""
    text = raw or ""
    text = re.sub(r"🔗\s*阅读原文：\S+", "", text)
    text = re.sub(r"via AI HOT\s*·\s*\S+", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def source_label(author: str | None) -> str:
    """从 RSS author 字段抽出可读来源名。"""
    if not author:
        return ""
    m = re.search(r"\((.+)\)\s*$", author)
    return (m.group(1).strip() if m else author.strip())


def gather_items(data: dict) -> list[dict]:
    """汇总各源 items，按时间新→旧。"""
    items: list[dict] = []
    for src in data.get("sources") or []:
        items.extend(src.get("items") or [])
    items.sort(key=lambda x: x.get("pub_date") or "", reverse=True)
    return items


def render_from_feed(data: dict) -> str:
    """按 category 分组渲染新闻列表（文左图右由模板 CSS 处理）。"""
    items = gather_items(data)
    if not items:
        return '<p class="empty-note">过去 24 小时无新条目。</p>'

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        cat = (it.get("category") or "").strip() or "未分类"
        by_cat[cat].append(it)

    known = [c for c in CATEGORY_ORDER if c in by_cat]
    rest = sorted(c for c in by_cat if c not in known)
    order = known + rest

    parts: list[str] = [
        f'<p class="section-meta">{len(items)} 条 · '
        f'<a href="https://aihot.virxact.com/" target="_blank" rel="noopener">打开 AI HOT</a></p>'
    ]
    for cat in order:
        parts.append(f'<h2 class="section-head">{escape(cat)}</h2>')
        for it in by_cat[cat]:
            title = escape(it.get("title") or "（无标题）")
            href = escape(it.get("link") or "#")
            body = escape(clean_summary(it.get("summary") or ""))
            src = escape(source_label(it.get("author")))
            meta = fmt_date((it.get("pub_date") or "")[:10]) or escape(
                it.get("pub_date_raw") or ""
            )
            img = it.get("image") or ""
            media = ""
            if img:
                media = (
                    f'<figure class="news-media">'
                    f'<img src="{escape(img)}" alt="" loading="lazy">'
                    f"</figure>"
                )
            parts.append(
                f'<article class="news-row">'
                f'<div class="news-body">'
                f'<time class="news-date">{meta}</time>'
                f'<h3 class="news-title"><a href="{href}" target="_blank" rel="noopener">{title}</a></h3>'
                f'{f"<p class=news-excerpt>{body}</p>" if body else ""}'
                f'{f"<p class=news-source>{src}</p>" if src else ""}'
                f'<a class="read-more" href="{href}" target="_blank" rel="noopener">阅读原文 ↗</a>'
                f"</div>{media}</article>"
            )
    return "\n".join(parts)


def main() -> None:
    """CLI：渲染 AIHOT fragment。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True, help="aihot.json")
    parser.add_argument("--out-dir", type=Path, required=True, help="sections 目录")
    parser.add_argument("--date", default="", help="YYYY-MM-DD（仅记录用）")
    args = parser.parse_args()

    data = json.loads(args.raw.read_text(encoding="utf-8"))
    frag = render_from_feed(data)
    summary = data.get("summary") or {}
    items_total = int(summary.get("items_total") or 0)
    health = summary.get("health_line") or f"今日成功抓取 AIHOT，共 {items_total} 条。"

    meta = {
        "section": "aihot",
        "health_line": health,
        "sources_ok": summary.get("sources_ok", 1),
        "sources_fail": summary.get("sources_fail", 0),
        "items_total": items_total,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "aihot.fragment.html").write_text(frag, encoding="utf-8")
    (args.out_dir / "aihot.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(health)


if __name__ == "__main__":
    main()
