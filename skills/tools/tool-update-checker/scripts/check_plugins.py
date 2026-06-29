#!/usr/bin/env python3
"""检查 Claude Code 已装插件是否有新版本。

读取 ~/.claude/plugins/installed_plugins.json（已装版本）+ 各 marketplace 的
marketplace.json（最新版本），对比输出。处理 5 种情况：
  - marketplace.json 直接声明 version（如 superpowers）
  - version 在插件子目录 plugin.json（source: "./xxx"，如 pm-skills、official）
  - marketplace 是 git clone → git fetch + 读 origin/HEAD
  - marketplace 是 GCS/directory 源 → 读本地缓存（标注局限性）

用法：python3 check_plugins.py
"""
import json, subprocess, os, sys
from collections import defaultdict

HOME = os.path.expanduser("~")
INSTALLED = f"{HOME}/.claude/plugins/installed_plugins.json"
MP_BASE = f"{HOME}/.claude/plugins/marketplaces"


def git(market, *args, timeout=30):
    mpath = os.path.join(MP_BASE, market)
    r = subprocess.run(["git", "-C", mpath, *args],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.returncode == 0


def read_marketplace_json(market, is_git):
    """读 marketplace.json：git 从 origin/HEAD，非 git 读本地。"""
    if is_git:
        git(market, "fetch", "-q", "origin")
        out, ok = git(market, "show", "origin/HEAD:.claude-plugin/marketplace.json")
        if ok:
            try:
                return json.loads(out)
            except Exception:
                pass
    local = os.path.join(MP_BASE, market, ".claude-plugin", "marketplace.json")
    if os.path.exists(local):
        try:
            return json.load(open(local))
        except Exception:
            pass
    return {"plugins": []}


def latest_version(market, entry, is_git):
    """从 marketplace 条目解析插件最新版本。"""
    # 1. 直接声明 version
    if entry.get("version"):
        return entry["version"]
    # 2. source 是子目录引用 → 读 plugin.json
    src = entry.get("source", "")
    if isinstance(src, str) and src.startswith("./"):
        rel = src[2:]
        rel_path = f"{rel}/.claude-plugin/plugin.json"
        if is_git:
            out, ok = git(market, "show", f"origin/HEAD:{rel_path}", timeout=15)
            if ok:
                try:
                    return json.loads(out).get("version", "?")
                except Exception:
                    pass
            return "?"
        local = os.path.join(MP_BASE, market, rel_path)
        if os.path.exists(local):
            try:
                return json.load(open(local)).get("version", "?")
            except Exception:
                pass
    return "?"


def main():
    installed = json.load(open(INSTALLED))["plugins"]

    # 按 marketplace 分组已装插件
    by_market = defaultdict(list)
    for k, v in installed.items():
        plugin, _, market = k.partition("@")
        cur = v[0].get("version", "unknown") if v else "?"
        by_market[market].append((plugin, cur))

    updates = []
    print(f"已装 {len(installed)} 个插件，来自 {len(by_market)} 个 marketplace\n")

    for market, plugins in sorted(by_market.items()):
        mpath = os.path.join(MP_BASE, market)
        is_git = os.path.isdir(os.path.join(mpath, ".git"))
        source_note = "" if is_git else " [非git/本地缓存,用/plugin确认]"
        mp_data = read_marketplace_json(market, is_git)
        entries = {p["name"]: p for p in mp_data.get("plugins", [])}

        for plugin, cur in plugins:
            new = latest_version(market, entries.get(plugin, {}), is_git)
            unknown = ("?" in str(new)) or (cur in ("unknown", "?"))
            if unknown:
                status = f"当前{cur}/最新{new}{source_note}"
            elif cur == new:
                status = "✅最新"
            else:
                status = f"⚠️ {cur}→{new}{source_note}"
                updates.append((plugin, market, cur, new))
            print(f"[{market}] {plugin}: {status}")

    print(f"\n=== 可更新: {len(updates)} 个 ===")
    for p, m, c, n in updates:
        print(f"  {p}@{m}: {c} → {n}")
    return updates


if __name__ == "__main__":
    main()
