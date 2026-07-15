#!/usr/bin/env python3
"""抓取指定日报板块的 RSS，过滤过去 N 小时，输出健康报告 JSON。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

# 默认超时与 UA：部分源拒空 UA
TIMEOUT_SEC = 18
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "daily-news-digest/1.0"
)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def skill_root() -> Path:
    """返回技能根目录（scripts/ 的上一级）。"""
    return Path(__file__).resolve().parent.parent


def load_feeds() -> dict[str, Any]:
    """加载 references/feeds.json。"""
    path = skill_root() / "references" / "feeds.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def now_utc() -> datetime:
    """当前 UTC 时间（带 tzinfo）。"""
    return datetime.now(timezone.utc)


def parse_pub_date(raw: str | None) -> datetime | None:
    """解析 RSS/Atom 常见时间格式为 UTC datetime。"""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    # ISO-8601 变体
    cleaned = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def local_text(el: ET.Element | None) -> str:
    """取元素文本（含简单 CDATA）。"""
    if el is None:
        return ""
    return (el.text or "").strip()


def find_child(parent: ET.Element, names: list[str]) -> ET.Element | None:
    """按本地标签名或 Clark 记法找第一个子元素。"""
    for child in parent:
        tag = child.tag
        local = tag.split("}")[-1] if "}" in tag else tag
        if local in names or tag in names:
            return child
    return None


def find_link(entry: ET.Element) -> str:
    """从 RSS item / Atom entry 提取链接。"""
    # RSS <link>text</link>
    link_el = find_child(entry, ["link"])
    if link_el is not None:
        href = link_el.attrib.get("href") or link_el.attrib.get("url")
        if href:
            return href.strip()
        if link_el.text and link_el.text.strip():
            return link_el.text.strip()
    # Atom 多个 link，优先 rel=alternate
    for child in entry:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local != "link":
            continue
        rel = child.attrib.get("rel", "alternate")
        href = child.attrib.get("href", "").strip()
        if href and rel in ("alternate", ""):
            return href
    guid = find_child(entry, ["guid", "id"])
    if guid is not None and (guid.text or "").startswith("http"):
        return guid.text.strip()
    return ""


def element_htmlish(el: ET.Element | None) -> str:
    """取元素文本；若无 text，拼接子树字符串（便于从 content:encoded 抽图）。"""
    if el is None:
        return ""
    text = (el.text or "").strip()
    if text:
        return text
    parts: list[str] = []
    for child in el:
        parts.append(ET.tostring(child, encoding="unicode"))
    return "".join(parts)


def extract_image_url(item_el: ET.Element, html_blobs: list[str]) -> str | None:
    """从 enclosure / media / HTML img 中取第一张可用配图 URL。"""
    for child in item_el:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "enclosure":
            url = (child.attrib.get("url") or "").strip()
            typ = (child.attrib.get("type") or "").lower()
            if url and (typ.startswith("image/") or re.search(r"\.(jpe?g|png|gif|webp)(\?|$)", url, re.I)):
                return url
        if local in ("content", "thumbnail"):
            url = (child.attrib.get("url") or "").strip()
            medium = (child.attrib.get("medium") or "").lower()
            typ = (child.attrib.get("type") or "").lower()
            if url and (medium == "image" or typ.startswith("image/") or re.search(r"\.(jpe?g|png|gif|webp)(\?|$)", url, re.I)):
                return url
    for blob in html_blobs:
        if not blob:
            continue
        m = re.search(
            r'<img[^>]+src=["\'](https?://[^"\']+)["\']',
            blob,
            flags=re.I,
        )
        if m:
            return m.group(1)
        m2 = re.search(
            r'(https?://[^\s"\'<>]+?\.(?:jpe?g|png|gif|webp)(?:\?[^\s"\'<>]*)?)',
            blob,
            flags=re.I,
        )
        if m2:
            return m2.group(1)
    return None


def strip_html(raw: str) -> str:
    """去掉 HTML 标签，压缩空白。"""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", text).strip()


def prepare_xml_bytes(raw: bytes) -> bytes:
    """清洗 feed 字节：去 BOM/前导空白，拒 HTML 伪装，定位真实 XML 起点。

    Dezeen 等源会在 `<?xml` 前塞一个空格；Frame 等已失效源会返回整页 HTML。
    """
    if not raw:
        raise ValueError("空响应")
    # UTF-8 BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    stripped = text.lstrip("\ufeff \t\r\n")
    head = stripped[:200].lower()
    if head.startswith("<!doctype html") or head.startswith("<html") or (
        "<html" in head and "<?xml" not in head and "<rss" not in head and "<feed" not in head
    ):
        raise ValueError("URL 返回 HTML 而非 RSS/Atom（源可能已停用 feed）")
    start = -1
    for marker in ("<?xml", "<rss", "<feed", "<RDF"):
        i = stripped.find(marker)
        if i >= 0 and (start < 0 or i < start):
            start = i
    if start < 0:
        raise ValueError("响应中未找到 RSS/Atom 根节点")
    return stripped[start:].encode("utf-8")


def parse_feed_items(xml_bytes: bytes) -> list[dict[str, Any]]:
    """把 RSS/Atom XML 解析成 item 列表（含可选 image）。"""
    xml_bytes = prepare_xml_bytes(xml_bytes)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"XML 解析失败: {e}") from e

    root_local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    items: list[dict[str, Any]] = []

    if root_local == "feed":
        entries = [c for c in root if c.tag.split("}")[-1] == "entry"]
        for entry in entries:
            title = local_text(find_child(entry, ["title"]))
            summary_el = find_child(entry, ["summary", "content"])
            summary_raw = element_htmlish(summary_el)
            published = local_text(
                find_child(entry, ["published", "updated", "date"])
            )
            image = extract_image_url(entry, [summary_raw])
            cat = local_text(find_child(entry, ["category"]))
            items.append(
                {
                    "title": title,
                    "link": find_link(entry),
                    "summary": strip_html(summary_raw)[:2000],
                    "image": image,
                    "category": cat or None,
                    "author": local_text(find_child(entry, ["author", "name"])) or None,
                    "pub_date_raw": published,
                    "pub_date": None,
                }
            )
    else:
        # RSS 2.0 channel/item
        channel_el = find_child(root, ["channel"])
        channel = channel_el if channel_el is not None else root
        for item in channel:
            local = item.tag.split("}")[-1] if "}" in item.tag else item.tag
            if local != "item":
                continue
            title = local_text(find_child(item, ["title"]))
            desc_el = find_child(item, ["description", "summary"])
            content_el = None
            for child in item:
                cl = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if cl == "encoded" or child.tag.endswith("}encoded"):
                    content_el = child
                    break
            desc_raw = element_htmlish(desc_el)
            content_raw = element_htmlish(content_el)
            pub = local_text(
                find_child(item, ["pubDate", "published", "date", "updated"])
            )
            if not pub:
                for child in item:
                    if child.tag.endswith("date"):
                        pub = local_text(child)
                        break
            image = extract_image_url(item, [content_raw, desc_raw])
            cat = local_text(find_child(item, ["category"]))
            author = local_text(find_child(item, ["author", "creator", "dc:creator"]))
            if not author:
                for child in item:
                    cl = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if cl in ("author", "creator") or child.tag.endswith("}creator"):
                        author = local_text(child)
                        break
            items.append(
                {
                    "title": title,
                    "link": find_link(item),
                    "summary": strip_html(desc_raw or content_raw)[:2000],
                    "image": image,
                    "category": cat or None,
                    "author": author or None,
                    "pub_date_raw": pub,
                    "pub_date": None,
                }
            )

    for it in items:
        dt = parse_pub_date(it["pub_date_raw"])
        it["pub_date"] = dt.isoformat() if dt else None
        it["_dt"] = dt
    return items


def http_get(url: str) -> bytes:
    """GET 原始字节；失败抛异常。"""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        return resp.read()


def swap_nitter_host(url: str, host: str) -> str:
    """把 Nitter URL 换成指定 mirror host。"""
    parsed = urlparse(url)
    return urlunparse(
        (parsed.scheme or "https", host, parsed.path, "", parsed.query, "")
    )


def candidate_urls(source: dict[str, Any], section: dict[str, Any]) -> list[str]:
    """生成主 URL + mirror 候选列表（去重保序）。"""
    urls: list[str] = []
    if source.get("handle"):
        mirrors = section.get("nitter_mirrors") or ["nitter.net"]
        for host in mirrors:
            urls.append(f"https://{host}/{source['handle']}/rss")
    else:
        primary = source.get("url") or ""
        if primary:
            urls.append(primary)
        for m in source.get("mirrors") or []:
            if m and m not in urls:
                urls.append(m)
        # 若主 URL 已是 nitter，仍可用全局 mirror 换 host
        if primary and "nitter" in primary:
            for host in section.get("nitter_mirrors") or []:
                swapped = swap_nitter_host(primary, host)
                if swapped not in urls:
                    urls.append(swapped)
    # 去重保序
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_one_source(
    source: dict[str, Any],
    section: dict[str, Any],
    cutoff: datetime,
) -> dict[str, Any]:
    """抓取单个订阅源，带 mirror 兜底；返回健康字段 + 过滤后条目。"""
    tried: list[dict[str, str]] = []
    last_error = ""
    for url in candidate_urls(source, section):
        try:
            raw = http_get(url)
            items = parse_feed_items(raw)
            kept = []
            handle = source.get("handle")
            source_name = source.get("name", source["id"])
            for it in items:
                dt = it.pop("_dt", None)
                # 无日期：保留但标记 unknown_date（稳定性上不丢标题流）
                if dt is None:
                    it["within_window"] = False
                    it["date_unknown"] = True
                    continue
                if dt >= cutoff:
                    it["within_window"] = True
                    it["date_unknown"] = False
                    it["source_id"] = source["id"]
                    it["source_name"] = source_name
                    it["source_handle"] = handle
                    it["source_domain"] = source.get("domain")
                    kept.append(it)
            kept.sort(key=lambda x: x.get("pub_date") or "", reverse=True)
            status = "ok" if kept else "empty"
            latest = kept[0]["pub_date"] if kept else None
            return {
                "id": source["id"],
                "name": source_name,
                "domain": source.get("domain"),
                "handle": handle,
                "status": status,
                "url_used": url,
                "urls_tried": [t["url"] for t in tried] + [url],
                "error": None,
                "item_count": len(kept),
                "latest_pub_date": latest,
                "items": kept,
            }
        except Exception as e:  # noqa: BLE001 — 单源失败要继续 mirror
            last_error = f"{type(e).__name__}: {e}"
            tried.append({"url": url, "error": last_error})
            continue

    return {
        "id": source["id"],
        "name": source.get("name", source["id"]),
        "domain": source.get("domain"),
        "handle": source.get("handle"),
        "status": "fail",
        "url_used": None,
        "urls_tried": [t["url"] for t in tried],
        "error": last_error or "all mirrors failed",
        "item_count": 0,
        "latest_pub_date": None,
        "items": [],
    }


def summarize(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总板块健康数字。"""
    ok = sum(1 for s in sources if s["status"] in ("ok", "empty"))
    fail = sum(1 for s in sources if s["status"] == "fail")
    items = sum(s["item_count"] for s in sources)
    # 「成功抓取」= 拿到了 feed（含空窗），失败 = 全 mirror 挂
    return {
        "sources_total": len(sources),
        "sources_ok": ok,
        "sources_fail": fail,
        "sources_with_items": sum(1 for s in sources if s["status"] == "ok"),
        "sources_empty": sum(1 for s in sources if s["status"] == "empty"),
        "items_total": items,
        "health_line": (
            f"今日成功抓取 {ok} 订阅源，抓取 {items} 条，失败 {fail} 订阅源。"
        ),
    }


def fetch_section(section_id: str, hours: float) -> dict[str, Any]:
    """抓取一个板块并返回完整 JSON 结构。"""
    feeds = load_feeds()
    if section_id not in feeds:
        raise SystemExit(f"未知板块: {section_id}; 可选: {', '.join(feeds)}")
    section = feeds[section_id]
    cutoff = now_utc() - timedelta(hours=hours)
    results = [
        fetch_one_source(src, section, cutoff) for src in section["sources"]
    ]
    return {
        "section": section_id,
        "label": section.get("label", section_id),
        "has_health_report": bool(section.get("has_health_report")),
        "window_hours": hours,
        "cutoff_utc": cutoff.isoformat(),
        "fetched_at": now_utc().isoformat(),
        "summary": summarize(results),
        "sources": results,
    }


def main() -> None:
    """CLI 入口：python fetch_section.py --section x-ai --out path.json"""
    parser = argparse.ArgumentParser(description="抓取日报板块 RSS（24h 窗口）")
    parser.add_argument(
        "--section",
        choices=["aihot", "x-ai", "design", "news"],
        help="板块 id（与 --all 互斥）",
    )
    parser.add_argument("--hours", type=float, default=24.0, help="时间窗小时数")
    parser.add_argument(
        "--out",
        type=Path,
        help="写入 JSON 路径；--all 时为目录",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="一次抓四个板块，写入 --out 目录",
    )
    args = parser.parse_args()

    if args.all:
        if not args.out:
            raise SystemExit("--all 需要 --out 指向目录")
        out_dir = args.out
        out_dir.mkdir(parents=True, exist_ok=True)
        bundle = {}
        for sid in ["aihot", "x-ai", "design", "news"]:
            data = fetch_section(sid, args.hours)
            path = out_dir / f"{sid}.json"
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            bundle[sid] = {
                "file": str(path),
                "summary": data["summary"],
            }
            print(f"[ok] {sid}: {data['summary']['health_line']}", file=sys.stderr)
        (out_dir / "_index.json").write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    if not args.section:
        raise SystemExit("请指定 --section 或使用 --all")
    data = fetch_section(args.section, args.hours)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(data["summary"]["health_line"], file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
