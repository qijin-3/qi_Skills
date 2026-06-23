#!/usr/bin/env python3
"""
技能注册表管理：扫描 skills/ 目录、维护 skills-registry.yaml、同步到 ~/.claude/skills。

用法:
  python scripts/skills-registry.py scan    # 扫描并更新注册表
  python scripts/skills-registry.py sync    # 将 sync=true 的技能软链接到 Claude Code
  python scripts/skills-registry.py readme  # 根据注册表更新 README.md
  python scripts/skills-registry.py all     # 执行 scan + readme + sync
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
REGISTRY_PATH = REPO_ROOT / "skills-registry.yaml"
README_PATH = REPO_ROOT / "README.md"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

KNOWN_CATEGORIES = {"engineering", "productivity", "misc", "deprecated"}
EXCLUDE_PATH_PARTS = {"node_modules", "deprecated", "template"}


@dataclass
class SkillEntry:
    """注册表中的单个技能条目。"""

    path: str
    name: str
    description: str
    category: str
    sync: bool

    def to_dict(self) -> dict:
        """转换为可写入 YAML 的字典。"""
        return {
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "sync": self.sync,
        }


def parse_frontmatter(skill_md: Path) -> tuple[str, str]:
    """
    从 SKILL.md 提取 name 和 description。

    Returns:
        (name, description) 元组；解析失败时 name 回退为目录名。
    """
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return skill_md.parent.name, ""

    meta = yaml.safe_load(match.group(1)) or {}
    name = str(meta.get("name") or skill_md.parent.name).strip()
    desc = meta.get("description", "")
    if isinstance(desc, list):
        description = " ".join(str(line).strip() for line in desc).strip()
    else:
        description = str(desc).strip()
    # 折叠 YAML 多行描述中的换行
    description = re.sub(r"\s+", " ", description)
    return name, description


def infer_category(rel_path: str) -> str:
    """
    根据 skills/ 下的相对路径推断分类。

    - skills/engineering/foo → engineering
    - skills/travel_journal/travel-journal → travel_journal
    - skills/idea-validator → uncategorized
    """
    parts = Path(rel_path).parts
    if len(parts) == 1:
        return "uncategorized"
    first = parts[0]
    if first in KNOWN_CATEGORIES:
        return first
    return first


def find_skill_dirs() -> list[Path]:
    """递归查找 skills/ 下所有包含 SKILL.md 的目录。"""
    if not SKILLS_DIR.is_dir():
        return []

    results: list[Path] = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        rel = skill_md.relative_to(SKILLS_DIR)
        if any(part in EXCLUDE_PATH_PARTS for part in rel.parts):
            continue
        results.append(skill_md.parent)
    return results


def load_registry() -> dict:
    """加载现有注册表；不存在时返回空结构。"""
    if not REGISTRY_PATH.exists():
        return {"version": 1, "skills": []}
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    data.setdefault("version", 1)
    data.setdefault("skills", [])
    return data


def scan_skills() -> tuple[list[SkillEntry], dict]:
    """
    扫描 skills/ 并与现有注册表合并。

    新发现的技能默认 sync=false；已存在条目保留 sync 标记。
    """
    registry = load_registry()
    existing_by_path = {s["path"]: s for s in registry.get("skills", [])}

    found_paths: set[str] = set()
    entries: list[SkillEntry] = []

    for skill_dir in find_skill_dirs():
        rel_from_repo = skill_dir.relative_to(REPO_ROOT).as_posix()
        rel_under_skills = skill_dir.relative_to(SKILLS_DIR).as_posix()
        found_paths.add(rel_from_repo)

        name, description = parse_frontmatter(skill_dir / "SKILL.md")
        category = infer_category(rel_under_skills)

        prev = existing_by_path.get(rel_from_repo, {})
        sync = bool(prev.get("sync", False))

        entries.append(
            SkillEntry(
                path=rel_from_repo,
                name=name,
                description=description,
                category=category,
                sync=sync,
            )
        )

    removed = set(existing_by_path.keys()) - found_paths
    changes = {
        "added": [e.path for e in entries if e.path not in existing_by_path],
        "removed": sorted(removed),
        "updated": [
            e.path
            for e in entries
            if e.path in existing_by_path
            and (
                existing_by_path[e.path].get("name") != e.name
                or existing_by_path[e.path].get("description") != e.description
                or existing_by_path[e.path].get("category") != e.category
            )
        ],
    }

    entries.sort(key=lambda e: (e.category, e.name))
    return entries, changes


def write_registry(entries: list[SkillEntry]) -> None:
    """将技能列表写入 skills-registry.yaml。"""
    header = """# 技能注册表 — 由 update-skills-docs / scripts/skills-registry.py 自动维护
#
# 字段说明:
#   path        - 技能目录（相对仓库根目录）
#   name        - SKILL.md frontmatter 中的 name（也是 ~/.claude/skills/ 下的链接名）
#   description - 技能作用简述（自动从 SKILL.md 同步）
#   category    - 分类（根据目录结构推断）
#   sync        - true = 软链接到 ~/.claude/skills/；false = 仅登记不同步
#
# 手动操作: 只需编辑 sync 字段（true/false），其余字段由扫描自动更新。

"""
    data = {"version": 1, "skills": [e.to_dict() for e in entries]}
    REGISTRY_PATH.write_text(
        header + yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def sync_to_claude(entries: list[SkillEntry]) -> dict:
    """
    将 sync=true 的技能软链接到 ~/.claude/skills/。

    同时清理此前由本仓库创建、现已取消 sync 的失效链接。
    """
    if CLAUDE_SKILLS_DIR.is_symlink():
        resolved = CLAUDE_SKILLS_DIR.resolve()
        if REPO_ROOT == resolved or str(resolved).startswith(str(REPO_ROOT) + "/"):
            print(
                f"error: {CLAUDE_SKILLS_DIR} 是指向本仓库的符号链接，请先移除后重试。",
                file=sys.stderr,
            )
            sys.exit(1)

    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    to_sync = {e.name: e for e in entries if e.sync}
    linked: list[str] = []
    skipped: list[str] = []
    removed: list[str] = []

    for entry in entries:
        if entry.sync:
            continue
        target = CLAUDE_SKILLS_DIR / entry.name
        if target.is_symlink():
            try:
                if target.resolve() == (REPO_ROOT / entry.path).resolve():
                    target.unlink()
                    removed.append(entry.name)
            except OSError:
                pass

    for name, entry in sorted(to_sync.items()):
        src = (REPO_ROOT / entry.path).resolve()
        target = CLAUDE_SKILLS_DIR / name

        if not src.is_dir():
            skipped.append(f"{name} (源目录不存在: {src})")
            continue

        if target.is_symlink():
            if target.resolve() == src:
                linked.append(f"{name} (已存在)")
                continue
            target.unlink()
        elif target.exists():
            if target.is_dir():
                import shutil

                shutil.rmtree(target)
            else:
                target.unlink()

        target.symlink_to(src)
        linked.append(name)

    return {"linked": linked, "skipped": skipped, "removed": removed}


def update_readme(entries: list[SkillEntry]) -> bool:
    """
    更新 README.md 的 ## Skills 列表 部分。

    仅展示 sync=true 的公开技能，按 category 分组。
    """
    if not README_PATH.exists():
        return False

    synced = [e for e in entries if e.sync]
    by_category: dict[str, list[SkillEntry]] = {}
    for e in synced:
        by_category.setdefault(e.category, []).append(e)

    category_titles = {
        "engineering": "Engineering",
        "productivity": "Productivity",
        "misc": "Misc",
        "uncategorized": "Uncategorized",
    }

    lines = ["## Skills 列表", ""]
    if not synced:
        lines.append("_暂无已同步的公开技能。在 skills-registry.yaml 中将技能的 sync 设为 true 后重新运行。_")
        lines.append("")
    else:
        for cat in sorted(by_category.keys()):
            title = category_titles.get(cat, cat.replace("_", " ").title())
            lines.append(f"### {title}")
            lines.append("")
            for e in sorted(by_category[cat], key=lambda x: x.name):
                lines.append(
                    f'- **[{e.name}](./{e.path}/SKILL.md)** — {e.description}'
                )
            lines.append("")

    new_section = "\n".join(lines).rstrip() + "\n"

    content = README_PATH.read_text(encoding="utf-8")
    pattern = r"## Skills 列表\n.*?(?=\n## |\Z)"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_section, content, count=1, flags=re.DOTALL)
    else:
        if "## License" in content:
            content = content.replace("## License", new_section + "\n## License")
        else:
            content = content.rstrip() + "\n\n" + new_section

    README_PATH.write_text(content, encoding="utf-8")
    return True


def print_summary(entries: list[SkillEntry], changes: dict, sync_result: dict | None = None) -> None:
    """打印操作摘要。"""
    synced = sum(1 for e in entries if e.sync)
    print(f"\n📋 注册表: {len(entries)} 个技能，{synced} 个已标记 sync")
    print(f"   文件: {REGISTRY_PATH}")

    if changes.get("added"):
        print(f"\n➕ 新增: {', '.join(changes['added'])}")
    if changes.get("removed"):
        print(f"\n➖ 移除: {', '.join(changes['removed'])}")
    if changes.get("updated"):
        print(f"\n✏️  元数据更新: {', '.join(changes['updated'])}")

    if sync_result:
        if sync_result["linked"]:
            print(f"\n🔗 已链接: {', '.join(sync_result['linked'])}")
        if sync_result["removed"]:
            print(f"\n🗑️  已取消链接: {', '.join(sync_result['removed'])}")
        if sync_result["skipped"]:
            print(f"\n⚠️  跳过: {', '.join(sync_result['skipped'])}")


def cmd_scan() -> list[SkillEntry]:
    """执行扫描并写入注册表。"""
    entries, changes = scan_skills()
    write_registry(entries)
    print_summary(entries, changes)
    return entries


def cmd_sync(entries: list[SkillEntry] | None = None) -> None:
    """执行 Claude Code 软链接同步。"""
    if entries is None:
        registry = load_registry()
        entries = [
            SkillEntry(
                path=s["path"],
                name=s["name"],
                description=s.get("description", ""),
                category=s.get("category", "uncategorized"),
                sync=bool(s.get("sync", False)),
            )
            for s in registry.get("skills", [])
        ]
    result = sync_to_claude(entries)
    print_summary(entries, {}, result)


def cmd_readme(entries: list[SkillEntry] | None = None) -> None:
    """更新 README.md。"""
    if entries is None:
        registry = load_registry()
        entries = [
            SkillEntry(
                path=s["path"],
                name=s["name"],
                description=s.get("description", ""),
                category=s.get("category", "uncategorized"),
                sync=bool(s.get("sync", False)),
            )
            for s in registry.get("skills", [])
        ]
    update_readme(entries)
    print(f"✅ 已更新 {README_PATH}")


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="管理 qi_Skills 技能注册表与 Claude Code 同步")
    parser.add_argument(
        "command",
        choices=["scan", "sync", "readme", "all"],
        help="scan=更新注册表, sync=软链接同步, readme=更新README, all=全部执行",
    )
    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan()
    elif args.command == "sync":
        cmd_sync()
    elif args.command == "readme":
        cmd_readme()
    elif args.command == "all":
        entries, changes = scan_skills()
        write_registry(entries)
        update_readme(entries)
        sync_result = sync_to_claude(entries)
        print_summary(entries, changes, sync_result)
        print(f"\n✅ 已更新 {README_PATH}")


if __name__ == "__main__":
    main()
