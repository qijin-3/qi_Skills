#!/usr/bin/env python3
"""日报输出路径解析：显式参数 > 环境变量 > Agent 空间 > 当前工作目录。"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

DIR_NAME = "daily-news-digest"

# Agent 工作区标记（OpenClaw / QClaw 等）
_WORKSPACE_MARKERS = ("AGENTS.md", "SOUL.md", "MEMORY.md", "IDENTITY.md")
_WORKSPACE_ENVS = (
    "DAILY_NEWS_DIGEST_ROOT",  # 最高优先（在 resolve 里单独处理）
    "OPENCLAW_WORKSPACE_DIR",
    "OPENCLAW_WORKSPACE",
    "QCLAW_WORKSPACE",
    "QCLAW_AGENT_HOME",
    "AGENT_WORKSPACE",
)


def today_str() -> str:
    """本地今日 YYYY-MM-DD。"""
    return date.today().isoformat()


def detect_agent_workspace(cwd: Path | None = None) -> Path | None:
    """若 cwd（或其祖先）像 Agent 空间，返回该根目录。"""
    start = (cwd or Path.cwd()).resolve()
    for p in [start, *start.parents]:
        if any((p / m).exists() for m in _WORKSPACE_MARKERS):
            return p
        # 兼容 profile 型默认目录
        if p.name.startswith("workspace") and (p / "skills").is_dir():
            return p
    for key in _WORKSPACE_ENVS[1:]:
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return None


def resolve_digest_root(explicit: str | Path | None = None) -> Path:
    """解析日报根目录（不含日期子目录）。

    优先级：
    1. 显式 `--root` / 传入路径
    2. 环境变量 `DAILY_NEWS_DIGEST_ROOT`
    3. 检测到的 Agent workspace 下的 `daily-news-digest/`
    4. 当前工作目录下的 `daily-news-digest/`
    """
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("DAILY_NEWS_DIGEST_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    ws = detect_agent_workspace()
    if ws is not None:
        return (ws / DIR_NAME).resolve()
    return (Path.cwd() / DIR_NAME).resolve()


def day_dir(root: Path, date_str: str | None = None) -> Path:
    """`{root}/{YYYY-MM-DD}`。"""
    return root / (date_str or today_str())


def layout(root: Path, date_str: str | None = None) -> dict[str, Path]:
    """返回当日目录结构路径。"""
    day = day_dir(root, date_str)
    return {
        "root": root,
        "day": day,
        "raw": day / "raw",
        "sections": day / "sections",
        "index": day / "index.html",
    }


def ensure_layout(root: Path, date_str: str | None = None) -> dict[str, Path]:
    """创建 raw/sections 并返回路径表。"""
    paths = layout(root, date_str)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["sections"].mkdir(parents=True, exist_ok=True)
    return paths
