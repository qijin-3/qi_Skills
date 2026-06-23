#!/usr/bin/env bash
set -euo pipefail

# 兼容入口：按 skills-sync.yaml 选择性同步技能到 ~/.claude/skills/
# 旧版会链接所有技能；现已改为仅同步 skills-sync.yaml 中列出的技能。
# 推荐直接使用: python3 scripts/skills-registry.py all

REPO="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$REPO/scripts/skills-registry.py" all
