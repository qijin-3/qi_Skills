#!/usr/bin/env python3
"""
将电影风格 CSS token 应用到游记 index.html。

用法（推荐，直接指定预设名称）：
  python3 apply-style.py --preset "冰雪禅意" --title "我的游记" --title-en "My Journal"

可用预设：
  黄金公路    暖金暗棕，史诗公路（文德斯）
  冰雪禅意    冷白深灰，极简克制（是枝裕和）
  大地翠绿    翠绿青蓝，自然纪录（纪录片风格）
  圣地金红    深黑金调，仪式感（贝托鲁奇）← 默认
  浪漫薄紫    淡紫米白，轻盈梦幻（法国新浪潮）
  极简黑白    纯黑白对比，现代感（安东尼奥尼）

或用 JSON 传入自定义 token：
  python3 apply-style.py --style-json /tmp/style.json --title "游记名称"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
MAP_JSON_PATH = ROOT / "data" / "map.json"

# ── 内置预设风格 ──────────────────────────────────────────────────
PRESETS: dict[str, dict] = {
    "黄金公路": {
        "ink": "#09070a", "ink_soft": "#14101a",
        "paper": "#e8d4a0",
        "red": "#c45a2a", "blue": "#5a7a9a",
        "white": "#ddc898", "green": "#5a7040",
        "tone": "#c4883c",
        "map_style": "cinematic-dark",
    },
    "冰雪禅意": {
        "ink": "#0c0c0e", "ink_soft": "#181820",
        "paper": "#e9e8e4",
        "red": "#a04040", "blue": "#4a6880",
        "white": "#d8d8d4", "green": "#4a6050",
        "tone": "#7a8fa6",
        "map_style": "paper-muted",
    },
    "大地翠绿": {
        "ink": "#060d09", "ink_soft": "#0f1a10",
        "paper": "#dcecd6",
        "red": "#8a4030", "blue": "#2a5870",
        "white": "#c8d8c0", "green": "#3d7a5e",
        "tone": "#4a8a5a",
        "map_style": "cinematic-warm",
    },
    "圣地金红": {
        "ink": "#0d0b08", "ink_soft": "#18120d",
        "paper": "#f4ead8",
        "red": "#b73525", "blue": "#2d5f8d",
        "white": "#e9dfcc", "green": "#3f6f4a",
        "tone": "#b88a3b",
        "map_style": "cinematic-dark",
    },
    "浪漫薄紫": {
        "ink": "#12101a", "ink_soft": "#1e1a2a",
        "paper": "#f0ecf8",
        "red": "#9a4060", "blue": "#4050a0",
        "white": "#e0dcea", "green": "#506070",
        "tone": "#8b6fa8",
        "map_style": "paper-muted",
    },
    "极简黑白": {
        "ink": "#080808", "ink_soft": "#141414",
        "paper": "#f0f0f0",
        "red": "#cc3333", "blue": "#336699",
        "white": "#d8d8d8", "green": "#447744",
        "tone": "#888888",
        "map_style": "paper-muted",
    },
}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """将 #rrggbb 转换为 rgba(r, g, b, alpha) 字符串。"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def apply_style(style: dict, title: str | None = None, title_en: str | None = None) -> None:
    """将风格 token 写入 index.html 和 data/map.json。"""
    if not HTML_PATH.exists():
        print(f"错误：找不到 {HTML_PATH}", file=sys.stderr)
        sys.exit(1)

    html = HTML_PATH.read_text(encoding="utf-8")

    # 推导 paper_dim（若未提供）
    paper = style.get("paper", "#f4ead8")
    tone = style.get("tone", "#b88a3b")
    tone_soft = style.get("tone_soft") or hex_to_rgba(tone, 0.18)
    paper_dim = style.get("paper_dim") or hex_to_rgba(paper, 0.72)

    # 推导 line / line_strong（若未提供，从 paper 推导）
    line = style.get("line") or hex_to_rgba(paper, 0.20)
    line_strong = style.get("line_strong") or hex_to_rgba(paper, 0.42)

    # 推导 ink_soft（若未提供）
    ink = style.get("ink", "#0d0b08")
    ink_soft = style.get("ink_soft") or ink  # 近似

    # body background 渐变用到 red 和 blue 的 RGB
    red = style.get("red", "#b73525")
    blue = style.get("blue", "#2d5f8d")
    red_rgba = hex_to_rgba(red, 0.12)
    blue_rgba = hex_to_rgba(blue, 0.12)

    # ── :root 块中的 CSS 变量替换 ──────────────────────────────────
    # 用正则精确匹配 :root { ... } 范围内的变量，避免误改其他选择器
    def replace_root_var(css_text: str, var_name: str, new_value: str) -> str:
        """在 :root 块内替换指定 CSS 变量的值。"""
        return re.sub(
            rf"(^|\n)(\s*{re.escape(var_name)}:\s*)([^;]+)(;)",
            lambda m: m.group(1) + m.group(2) + new_value + m.group(4),
            css_text,
            count=1,
        )

    # 找到 :root 块的范围
    root_match = re.search(r":root\s*\{([^}]+)\}", html, re.DOTALL)
    if not root_match:
        print("警告：找不到 :root 块，CSS 变量替换跳过", file=sys.stderr)
    else:
        root_block = root_match.group(0)
        new_root = root_block
        var_map = {
            "--ink": ink,
            "--ink-soft": ink_soft,
            "--paper": paper,
            "--paper-dim": paper_dim,
            "--line": line,
            "--line-strong": line_strong,
            "--red": red,
            "--blue": style.get("blue", "#2d5f8d"),
            "--white": style.get("white", "#e9dfcc"),
            "--green": style.get("green", "#3f6f4a"),
            "--blackGold": tone,
            "--tone-soft": tone_soft,
        }
        for var_name, value in var_map.items():
            new_root = replace_root_var(new_root, var_name, value)
        html = html.replace(root_block, new_root, 1)

    # ── body background 渐变（硬编码 red/blue 的 rgba） ────────────
    html = re.sub(
        r"radial-gradient\(circle at 18% 12%,\s*rgba\([^)]+\),\s*transparent 30%\)",
        f"radial-gradient(circle at 18% 12%, {red_rgba}, transparent 30%)",
        html,
    )
    html = re.sub(
        r"radial-gradient\(circle at 78% 64%,\s*rgba\([^)]+\),\s*transparent 34%\)",
        f"radial-gradient(circle at 78% 64%, {blue_rgba}, transparent 34%)",
        html,
    )

    # ── 入口页静态标题（HTML 文本节点） ──────────────────────────────
    if title:
        html = re.sub(
            r'(<h1 class="entry-gate__title"[^>]*>)[^<]*(</h1>)',
            rf'\g<1>{title}\2',
            html,
        )

    HTML_PATH.write_text(html, encoding="utf-8")

    # ── 更新 data/map.json ────────────────────────────────────────
    if MAP_JSON_PATH.exists():
        cfg = json.loads(MAP_JSON_PATH.read_text(encoding="utf-8"))
        if style.get("map_style"):
            cfg["activeStyle"] = style["map_style"]
        if title:
            cfg["journalTitle"] = title
        if title_en:
            cfg["journalTitleEn"] = title_en
        # 同步 routes.full.color（用 paper 颜色推导）
        cfg.setdefault("routes", {}).setdefault("full", {})
        cfg["routes"]["full"]["color"] = hex_to_rgba(paper, 0.16)
        MAP_JSON_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"✅ 风格已应用：ink={ink}  paper={paper}  tone={tone}  地图={style.get('map_style','unchanged')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="将电影风格 token 应用到游记 HTML")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preset", choices=list(PRESETS.keys()),
                       help=f"内置预设名称，可选：{', '.join(PRESETS.keys())}")
    group.add_argument("--style-json", help="包含自定义 CSS token 的 JSON 文件路径")
    parser.add_argument("--title", default=None, help="游记中文标题")
    parser.add_argument("--title-en", default=None, help="游记英文副标题")
    args = parser.parse_args()

    if args.preset:
        style = PRESETS[args.preset]
        print(f"使用预设：{args.preset}")
    else:
        style_path = Path(args.style_json)
        if not style_path.exists():
            print(f"错误：找不到 {style_path}", file=sys.stderr)
            return 1
        style = json.loads(style_path.read_text(encoding="utf-8"))

    apply_style(style, title=args.title, title_en=args.title_en)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
