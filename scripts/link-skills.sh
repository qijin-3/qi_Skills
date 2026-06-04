#!/usr/bin/env bash
set -euo pipefail

# 将仓库中的所有 skills 链接到 ~/.claude/skills
# 扫描两个目录：skills/ (公开) 和 .claude/skills/ (私有)
# 这样本地 Claude CLI 就可以使用这些 skills

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude/skills"

# 检测 ~/.claude/skills 是否是指向本仓库的符号链接
# 如果是，我们会在本仓库的 skills/ 树中创建 per-skill 符号链接
# 这会污染工作副本，所以需要检测并退出
if [ -L "$DEST" ]; then
  resolved="$(readlink -f "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run; the script will recreate it as a real dir." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

# 扫描 skills/ 目录（公开 skills）
if [ -d "$REPO/skills" ]; then
  find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0 |
  while IFS= read -r -d '' skill_md; do
    src="$(dirname "$skill_md")"
    name="$(basename "$src")"
    target="$DEST/$name"

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $src"
  done
fi

# 扫描 .claude/skills/ 目录（私有 meta skills）
if [ -d "$REPO/.claude/skills" ]; then
  find "$REPO/.claude/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0 |
  while IFS= read -r -d '' skill_md; do
    src="$(dirname "$skill_md")"
    name="$(basename "$src")"
    target="$DEST/$name"

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $src (private)"
  done
fi
