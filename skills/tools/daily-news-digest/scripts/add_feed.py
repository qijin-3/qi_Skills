#!/usr/bin/env python3
"""向 feeds.json 添加订阅源，并按 URL/名称自动归入 aihot / x-ai / design / news。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SKILL_ROOT = Path(__file__).resolve().parent.parent
FEEDS_PATH = SKILL_ROOT / "references" / "feeds.json"

SECTIONS = ("aihot", "x-ai", "design", "news")

DESIGN_HINTS = (
    "design",
    "dezeen",
    "yankodesign",
    "yanko",
    "core77",
    "abduzeedo",
    "yellowtrace",
    "archdaily",
    "maltm",
    "itsnicethat",
    "nice that",
    "designmilk",
    "design-milk",
    "designboom",
    "frameweb",
    "wallpaper",
    "smashingmagazine",
    "smashing",
    "industrial design",
    "工业设计",
    "产品设计",
    "视觉设计",
)
NEWS_HINTS = (
    "news",
    "rss",
    "weixin",
    "fortune",
    "economist",
    "guancha",
    "thepaper",
    "idaily",
    "reuters",
    "bbc",
    "nyt",
    "新闻",
    "时政",
    "财经",
)
AIHOT_HINTS = ("aihot.virxact", "aihot")
X_HOSTS = ("x.com", "twitter.com", "nitter.", "mobile.twitter.com")


def load_feeds() -> dict[str, Any]:
    """读取 feeds.json。"""
    return json.loads(FEEDS_PATH.read_text(encoding="utf-8"))


def save_feeds(data: dict[str, Any]) -> None:
    """写回 feeds.json（缩进 2）。"""
    FEEDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def slug_id(text: str) -> str:
    """从名称/URL 生成稳定 id。"""
    s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", (text or "").strip()).strip("-")
    s = s.lower() or "feed"
    return s[:48]


def haystack(url: str, name: str, domain: str) -> str:
    """拼检索串。"""
    return " ".join([url or "", name or "", domain or ""]).lower()


def classify(
    *,
    url: str = "",
    name: str = "",
    handle: str = "",
    domain: str = "",
) -> str:
    """推断板块；x handle 优先归 x-ai。"""
    if handle.strip():
        return "x-ai"
    h = haystack(url, name, domain)
    host = (urlparse(url).hostname or "").lower()
    path = (urlparse(url).path or "").lower()

    if any(k in h for k in AIHOT_HINTS) or "aihot.virxact" in host:
        return "aihot"
    if handle or any(x in host or x in path for x in X_HOSTS) or "/rss/" in path and "nitter" in h:
        # 纯 twitter 主页 / nitter
        if any(x in host for x in X_HOSTS) or "nitter" in host:
            return "x-ai"
    if any(k in h for k in DESIGN_HINTS):
        return "design"
    if any(k in h for k in NEWS_HINTS):
        return "news"
    # 默认新闻栏（通用 RSS 最常见）
    return "news"


def extract_handle_from_url(url: str) -> str | None:
    """从 x.com / nitter URL 抽 handle。"""
    try:
        u = urlparse(url)
    except ValueError:
        return None
    host = (u.hostname or "").lower()
    parts = [p for p in (u.path or "").split("/") if p]
    if not parts:
        return None
    if any(h in host for h in ("x.com", "twitter.com", "mobile.twitter.com")) or "nitter" in host:
        cand = parts[0].lstrip("@")
        if cand and cand not in ("i", "home", "search", "intent"):
            return cand
    return None


def existing_ids(feeds: dict[str, Any]) -> set[str]:
    """所有源 id。"""
    ids: set[str] = set()
    for sec in SECTIONS:
        for src in feeds.get(sec, {}).get("sources") or []:
            if src.get("id"):
                ids.add(src["id"])
    return ids


def unique_id(feeds: dict[str, Any], preferred: str) -> str:
    """避免 id 冲突。"""
    base = slug_id(preferred)
    ids = existing_ids(feeds)
    if base not in ids:
        return base
    n = 2
    while f"{base}-{n}" in ids:
        n += 1
    return f"{base}-{n}"


def build_source(
    *,
    section: str,
    url: str,
    name: str,
    handle: str,
    domain: str,
    source_id: str,
) -> dict[str, Any]:
    """按板块拼 sources 条目。"""
    if section == "x-ai":
        h = handle or extract_handle_from_url(url) or source_id
        return {
            "id": source_id,
            "name": name or f"@{h}",
            "handle": h.lstrip("@"),
        }
    entry: dict[str, Any] = {
        "id": source_id,
        "name": name or source_id,
        "url": url,
        "mirrors": [],
    }
    if section in ("design", "news") and domain:
        entry["domain"] = domain
    elif section == "design":
        entry["domain"] = domain or "综合设计"
    elif section == "news":
        entry["domain"] = domain or "综合新闻"
    return entry


def add_source(
    *,
    url: str = "",
    name: str = "",
    handle: str = "",
    domain: str = "",
    section: str | None = None,
    source_id: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """添加源并返回结果摘要。"""
    if not url and not handle:
        raise SystemExit("需要 --url 或 --handle")
    h = handle.lstrip("@") if handle else ""
    if not h and url:
        h = extract_handle_from_url(url) or ""

    feeds = load_feeds()
    sec = section or classify(url=url, name=name, handle=h, domain=domain)
    if sec not in SECTIONS:
        raise SystemExit(f"未知板块: {sec}，可选 {SECTIONS}")

    preferred = source_id or h or name or urlparse(url).hostname or "feed"
    sid = unique_id(feeds, preferred)
    entry = build_source(
        section=sec,
        url=url,
        name=name,
        handle=h,
        domain=domain,
        source_id=sid,
    )

    # 去重：同 url 或同 handle
    sources: list[dict[str, Any]] = feeds.setdefault(sec, {}).setdefault("sources", [])
    for existing in sources:
        if entry.get("url") and existing.get("url") == entry["url"]:
            return {"action": "exists", "section": sec, "source": existing}
        if entry.get("handle") and existing.get("handle") == entry["handle"]:
            return {"action": "exists", "section": sec, "source": existing}

    if not dry_run:
        sources.append(entry)
        save_feeds(feeds)

    return {
        "action": "added" if not dry_run else "would_add",
        "section": sec,
        "classified": section is None,
        "source": entry,
        "feeds_path": str(FEEDS_PATH),
    }


def list_sources() -> list[dict[str, Any]]:
    """列出全部源。"""
    feeds = load_feeds()
    rows = []
    for sec in SECTIONS:
        for src in feeds.get(sec, {}).get("sources") or []:
            rows.append({"section": sec, **src})
    return rows


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="添加或列出日报订阅源")
    parser.add_argument("--url", default="", help="RSS/Atom URL（x-ai 可用主页 URL）")
    parser.add_argument("--handle", default="", help="X/Twitter handle → 自动进 x-ai")
    parser.add_argument("--name", default="", help="显示名")
    parser.add_argument("--domain", default="", help="design/news 的子域标签")
    parser.add_argument(
        "--section",
        choices=SECTIONS,
        default=None,
        help="强制板块；省略则自动分类",
    )
    parser.add_argument("--id", default="", help="自定义源 id")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写文件")
    parser.add_argument("--list", action="store_true", help="列出当前全部源")
    parser.add_argument("--classify-only", action="store_true", help="只打印分类结果")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(list_sources(), ensure_ascii=False, indent=2))
        return

    if args.classify_only:
        h = args.handle.lstrip("@")
        sec = classify(url=args.url, name=args.name, handle=h, domain=args.domain)
        print(json.dumps({"section": sec}, ensure_ascii=False))
        return

    result = add_source(
        url=args.url,
        name=args.name,
        handle=args.handle,
        domain=args.domain,
        section=args.section,
        source_id=args.id,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
