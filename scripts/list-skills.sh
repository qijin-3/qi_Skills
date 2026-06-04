#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO"
# 只列出 skills/ 目录下的 skills（不包括 .claude/skills）
find ./skills -name SKILL.md -not -path '*/node_modules/*' 2>/dev/null | sed 's|^./||' | sort
