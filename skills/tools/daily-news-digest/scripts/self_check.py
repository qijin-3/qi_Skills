#!/usr/bin/env python3
"""离线自检：时间解析、24h 过滤、mirror URL、组装占位替换。失败则 exit 1。"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compose_digest  # noqa: E402
import fetch_section as fs  # noqa: E402
import render_aihot_fragment as raf  # noqa: E402


def assert_true(cond: bool, msg: str) -> None:
    """断言助手。"""
    if not cond:
        raise AssertionError(msg)


def main() -> None:
    """跑一组不依赖外网的稳定性检查。"""
    # 时间解析
    dt = fs.parse_pub_date("Wed, 15 Jul 2026 00:00:39 GMT")
    assert_true(dt is not None and dt.year == 2026, "RFC822 解析失败")

    # mirror 候选
    feeds = fs.load_feeds()
    src = {"id": "sama", "name": "Sam Altman", "handle": "sama"}
    urls = fs.candidate_urls(src, feeds["x-ai"])
    assert_true(len(urls) >= 2, "Nitter mirror 数量不足")
    assert_true(all(u.endswith("/sama/rss") for u in urls), "handle 路径错误")

    # RSS 解析 + 窗口
    sample = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>Keep me</title>
        <link>https://example.com/a</link>
        <pubDate>Wed, 15 Jul 2026 00:00:39 GMT</pubDate>
      </item>
      <item>
        <title>Drop me</title>
        <link>https://example.com/b</link>
        <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
      </item>
    </channel></rss>"""
    items = fs.parse_feed_items(sample)
    cutoff = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    kept = [i for i in items if i.get("_dt") and i["_dt"] >= cutoff]
    assert_true(len(kept) == 1 and kept[0]["title"] == "Keep me", "24h 过滤错误")

    # AIHOT render + compose
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        raw = out / "raw"
        sections = out / "sections"
        raw.mkdir()
        sections.mkdir()
        aihot = {
            "section": "aihot",
            "summary": {
                "sources_ok": 1,
                "sources_fail": 0,
                "items_total": 1,
                "health_line": "今日成功抓取 1 订阅源，抓取 1 条，失败 0 订阅源。",
            },
            "sources": [
                {
                    "items": [
                        {
                            "title": "Hello",
                            "link": "https://example.com/d",
                            "summary": "s",
                            "pub_date": "2026-07-15T00:00:00+00:00",
                        }
                    ]
                }
            ],
        }
        (raw / "aihot.json").write_text(json.dumps(aihot), encoding="utf-8")
        for sid in ("x-ai", "design", "news"):
            empty = {
                "section": sid,
                "sources": [],
                "summary": {
                    "health_line": f"今日成功抓取 0 订阅源，抓取 0 条，失败 0 订阅源。",
                    "sources_ok": 0,
                    "sources_fail": 0,
                    "items_total": 0,
                },
            }
            (raw / f"{sid}.json").write_text(json.dumps(empty), encoding="utf-8")
            (sections / f"{sid}.fragment.html").write_text(
                f"<p>{sid}</p>", encoding="utf-8"
            )
            (sections / f"{sid}.meta.json").write_text(
                json.dumps(
                    {
                        "section": sid,
                        "health_line": empty["summary"]["health_line"],
                        "sources_ok": 0,
                        "sources_fail": 0,
                        "items_total": 0,
                    }
                ),
                encoding="utf-8",
            )

        frag, meta = raf.render(aihot)
        assert_true("Hello" in frag and "example.com/d" in frag, "AIHOT fragment 缺链接")
        (sections / "aihot.fragment.html").write_text(frag, encoding="utf-8")
        (sections / "aihot.meta.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )

        index = compose_digest.compose(out, "2026-07-15")
        html = index.read_text(encoding="utf-8")
        assert_true("<title>2026-07-15</title>" in html, "title 不是日期")
        assert_true('data-tab="health"' in html, "缺健康 Tab")
        assert_true("health-group" in html, "健康 Tab 未分组")
        assert_true("<details" in html, "健康分组未用可折叠 details")
        assert_true("{{" not in html, "仍有未替换占位符")
        assert_true("Hello" in html, "AIHOT 内容未装入")

        # 配图抽取：content:encoded img
        sample = b"""<?xml version="1.0"?>
        <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
        <channel><item>
          <title>Pic</title>
          <link>https://example.com/p</link>
          <pubDate>Wed, 15 Jul 2026 00:00:39 GMT</pubDate>
          <description><![CDATA[hi]]></description>
          <content:encoded><![CDATA[<img src="https://cdn.example.com/a.jpg" />]]></content:encoded>
        </item></channel></rss>"""
        parsed = fs.parse_feed_items(sample)
        assert_true(
            parsed and parsed[0].get("image") == "https://cdn.example.com/a.jpg",
            "未能从 content:encoded 抽图",
        )

        # Dezeen 类前导空格
        spaced = b' <?xml version="1.0"?><rss version="2.0"><channel><item>'
        spaced += b"<title>A</title><link>https://x.test</link>"
        spaced += b"<pubDate>Wed, 15 Jul 2026 00:00:39 GMT</pubDate>"
        spaced += b"</item></channel></rss>"
        assert_true(fs.parse_feed_items(spaced)[0]["title"] == "A", "前导空格 XML 未清洗")

        # HTML 伪装应失败
        try:
            fs.parse_feed_items(b"<!DOCTYPE html><html><body>nope</body></html>")
            raise AssertionError("HTML 应被拒绝")
        except ValueError:
            pass

    print("self_check OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"self_check FAIL: {e}", file=sys.stderr)
        sys.exit(1)
