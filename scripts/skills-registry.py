#!/usr/bin/env python3
"""
技能管理：扫描 skills/、维护 skills-sync.yaml、同步到 ~/.claude/skills。

用法:
  python scripts/skills-registry.py scan    # 扫描并更新 skills-sync.yaml
  python scripts/skills-registry.py sync    # 软链接同步到 Claude Code
  python scripts/skills-registry.py readme  # 更新 README.md
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
SYNC_PATH = REPO_ROOT / "skills-sync.yaml"
LEGACY_REGISTRY_PATH = REPO_ROOT / "skills-registry.yaml"
README_PATH = REPO_ROOT / "README.md"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

UNSYNC_KEY = "unsync"
SYNC_HEADER = """# 技能同步配置
#
# 在 sync / unsync 之间移动技能 name 即可（复制粘贴）。
# name 来自 SKILL.md frontmatter，不是目录名。
# 修改后运行: python3 scripts/skills-registry.py all

"""

KNOWN_CATEGORIES = {"engineering", "productivity", "misc", "deprecated"}
EXCLUDE_PATH_PARTS = {"node_modules", "deprecated", "template"}

GROUP_TITLES = {
    "engineering": "Engineering",
    "productivity": "Productivity",
    "misc": "Misc",
    "product design": "Product Design",
    "travel_journal": "Travel Journal",
    "meeting": "Meeting",
}


@dataclass
class SkillEntry:
    """扫描到的单个技能条目。"""

    path: str
    name: str
    description: str
    summary: str
    group: str
    sync: bool = False

    @property
    def folder_name(self) -> str:
        """返回技能所在目录名。"""
        return Path(self.path).name


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
    description = re.sub(r"\s+", " ", description)
    return name, description


def summarize_description(description: str, max_len: int = 48) -> str:
    """
    将 SKILL.md 的完整 description 压缩为 README 用的一句话摘要。
    """
    text = description.strip()
    if not text:
        return ""

    for sep in [" —— ", " — ", " - "]:
        if sep in text:
            title, rest = text.split(sep, 1)
            title, rest = title.strip(), rest.strip()
            if len(title) >= 4 and (not rest or len(rest) > max_len):
                text = title
            elif len(title) >= 6:
                text = title
            elif rest:
                text = rest
            break

    cut_markers = [
        "当用户说",
        "当用户",
        "适用于：",
        "适用于",
        "触发词",
        "Use when",
        "也适用于",
    ]
    for marker in cut_markers:
        idx = text.find(marker)
        if idx > 12:
            text = text[:idx].strip()
            break

    for sep in ["。", ". "]:
        if sep in text:
            text = text.split(sep, 1)[0].strip()
            break

    if "：" in text:
        head, _tail = text.split("：", 1)
        if len(head) <= max_len:
            text = head.strip()

    if "，" in text:
        comma_idx = text.find("，")
        if comma_idx < max_len:
            text = text.split("，", 1)[0].strip()

    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    if ascii_ratio > 0.75 and len(text.split()) > 5:
        words = text.split()
        text = " ".join(words[:5])
        if len(words) > 5:
            text += "…"

    text = text.rstrip("。，,;； ")
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip("，,;； （(") + "…"
    return text


def infer_group(rel_under_skills: str) -> str:
    """根据 skills/ 下的相对路径推断分组。"""
    parts = Path(rel_under_skills).parts
    if len(parts) == 1:
        return parts[0]
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


def load_sync_lists() -> tuple[list[str], list[str]]:
    """从 skills-sync.yaml 读取 sync / unsync 两个列表。"""
    if not SYNC_PATH.exists():
        return [], []

    data = yaml.safe_load(SYNC_PATH.read_text(encoding="utf-8")) or {}
    sync = _normalize_name_list(data.get("sync", []))
    unsync = _normalize_name_list(
        data.get(UNSYNC_KEY, data.get("不同步", []))
    )
    return sync, unsync


def _normalize_name_list(names: object) -> list[str]:
    """将 YAML 列表规范化为去重保序的 name 列表。"""
    if not isinstance(names, list):
        return []
    seen: set[str] = set()
    result: list[str] = []
    for name in names:
        clean = str(name).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def write_sync_lists(sync_names: list[str], unsync_names: list[str]) -> None:
    """写入 skills-sync.yaml（sync / unsync 两组，固定缩进便于复制粘贴）。"""
    sync_set = set(sync_names)
    unsync_clean = [name for name in unsync_names if name not in sync_set]
    lines = [SYNC_HEADER.rstrip(), "sync:"]
    for name in sync_names:
        lines.append(f"  - {name}")
    lines.append(f"{UNSYNC_KEY}:")
    for name in unsync_clean:
        lines.append(f"  - {name}")
    lines.append("")
    SYNC_PATH.write_text("\n".join(lines), encoding="utf-8")


def migrate_legacy_registry() -> None:
    """从旧版 skills-registry.yaml 迁移后删除该文件。"""
    if not LEGACY_REGISTRY_PATH.exists():
        return

    data = yaml.safe_load(LEGACY_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    sync_names: list[str] = []

    if "groups" in data:
        for group_skills in data.get("groups", {}).values():
            for skill in group_skills or []:
                if skill.get("sync"):
                    sync_names.append(skill["name"])
    else:
        for skill in data.get("skills", []):
            if skill.get("sync"):
                sync_names.append(skill["name"])

    existing_sync, existing_unsync = load_sync_lists()
    if not existing_sync and not existing_unsync and sync_names:
        write_sync_lists(_normalize_name_list(sync_names), [])

    LEGACY_REGISTRY_PATH.unlink()


def reconcile_sync_file(entries: list[SkillEntry]) -> tuple[list[SkillEntry], dict]:
    """
    根据扫描结果更新 skills-sync.yaml，保留用户手动分组。

    新技能默认加入 unsync；已删除技能从两组移除。
    """
    migrate_legacy_registry()
    all_names = {entry.name for entry in entries}
    old_sync, old_unsync = load_sync_lists()
    old_sync_set, old_unsync_set = set(old_sync), set(old_unsync)

    new_sync = [name for name in old_sync if name in all_names]
    new_unsync = [name for name in old_unsync if name in all_names and name not in new_sync]

    for entry in entries:
        if entry.name not in new_sync and entry.name not in new_unsync:
            new_unsync.append(entry.name)

    overlap = set(new_sync) & set(new_unsync)
    if overlap:
        new_unsync = [name for name in new_unsync if name not in overlap]

    new_sync_set, new_unsync_set = set(new_sync), set(new_unsync)
    changes = {
        "new_skills": [e.name for e in entries if e.name not in old_sync_set and e.name not in old_unsync_set],
        "removed_skills": sorted((old_sync_set | old_unsync_set) - all_names),
        "moved_to_sync": sorted(new_sync_set - old_sync_set),
        "moved_to_unsync": sorted(new_unsync_set - old_unsync_set),
    }

    write_sync_lists(new_sync, new_unsync)

    for entry in entries:
        entry.sync = entry.name in new_sync_set

    return entries, changes


def scan_skills(reconcile: bool = True) -> tuple[list[SkillEntry], dict]:
    """扫描 skills/ 目录；可选更新 skills-sync.yaml。"""
    entries: list[SkillEntry] = []

    for skill_dir in find_skill_dirs():
        rel_from_repo = skill_dir.relative_to(REPO_ROOT).as_posix()
        rel_under_skills = skill_dir.relative_to(SKILLS_DIR).as_posix()
        name, description = parse_frontmatter(skill_dir / "SKILL.md")
        entries.append(
            SkillEntry(
                path=rel_from_repo,
                name=name,
                description=description,
                summary=summarize_description(description),
                group=infer_group(rel_under_skills),
            )
        )

    entries.sort(key=lambda item: (item.group, item.name))

    if reconcile:
        return reconcile_sync_file(entries)

    sync_names, _ = load_sync_lists()
    sync_set = set(sync_names)
    for entry in entries:
        entry.sync = entry.name in sync_set
    return entries, {}


def points_to_repo(path: Path) -> bool:
    """判断路径是否指向本仓库 skills 目录下。"""
    try:
        resolved = path.resolve()
        skills_root = SKILLS_DIR.resolve()
        return resolved == skills_root or str(resolved).startswith(str(skills_root) + "/")
    except OSError:
        return False


def remove_repo_symlink(name: str) -> bool:
    """若 ~/.claude/skills/<name> 指向本仓库则移除。"""
    target = CLAUDE_SKILLS_DIR / name
    if not target.is_symlink():
        return False
    if points_to_repo(target):
        target.unlink()
        return True
    return False


def cleanup_repo_symlinks(entries: list[SkillEntry]) -> list[str]:
    """
    清理不应保留的本仓库软链接。

    覆盖：移到 unsync、从 sync 删除、以及 ~/.claude/skills 中残留的本仓库链接。
    """
    should_sync = {entry.name for entry in entries if entry.sync}
    removed: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        if not entry.sync and remove_repo_symlink(entry.name):
            removed.append(entry.name)
            seen.add(entry.name)

    if CLAUDE_SKILLS_DIR.is_dir():
        for target in CLAUDE_SKILLS_DIR.iterdir():
            if not target.is_symlink() or not points_to_repo(target):
                continue
            name = target.name
            if name in should_sync:
                continue
            target.unlink()
            if name not in seen:
                removed.append(name)
                seen.add(name)

    return sorted(removed)


def sync_to_claude(entries: list[SkillEntry]) -> dict:
    """将 sync 列表中的技能软链接到 ~/.claude/skills/，并清理已取消同步的链接。"""
    if CLAUDE_SKILLS_DIR.is_symlink():
        resolved = CLAUDE_SKILLS_DIR.resolve()
        if REPO_ROOT == resolved or str(resolved).startswith(str(REPO_ROOT) + "/"):
            print(
                f"error: {CLAUDE_SKILLS_DIR} 是指向本仓库的符号链接，请先移除后重试。",
                file=sys.stderr,
            )
            sys.exit(1)

    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    removed = cleanup_repo_symlinks(entries)
    linked: list[str] = []
    skipped: list[str] = []
    name_to_entry = {entry.name: entry for entry in entries}

    sync_names, _ = load_sync_lists()
    for name in sync_names:
        entry = name_to_entry.get(name)
        if entry is None:
            skipped.append(f"{name} (仓库中未找到该技能)")
            remove_repo_symlink(name)
            continue

        src = (REPO_ROOT / entry.path).resolve()
        target = CLAUDE_SKILLS_DIR / name

        if not src.is_dir():
            skipped.append(f"{name} (源目录不存在: {src})")
            continue

        if target.is_symlink():
            if target.resolve() == src:
                linked.append(f"{name} (已存在)")
                continue
            if points_to_repo(target):
                target.unlink()
            else:
                skipped.append(f"{name} (已存在且指向其他位置: {target.resolve()})")
                continue
        elif target.exists():
            skipped.append(f"{name} (目标已存在且非本仓库软链接)")
            continue

        target.symlink_to(src)
        linked.append(name)

    return {"linked": linked, "skipped": skipped, "removed": removed}


def group_entries(entries: list[SkillEntry]) -> dict[str, list[SkillEntry]]:
    """按分组整理技能列表。"""
    grouped: dict[str, list[SkillEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.group, []).append(entry)
    for group in grouped:
        grouped[group].sort(key=lambda item: item.name)
    return grouped


def format_group_title(group: str) -> str:
    """将内部分组名转为展示标题。"""
    return GROUP_TITLES.get(group, group.replace("_", " ").title())


def build_directory_tree(entries: list[SkillEntry]) -> str:
    """生成 skills/ 目录树（含一句话摘要）。"""
    grouped = group_entries(entries)
    lines = ["```", "skills/"]

    root_groups = sorted(grouped.keys())
    for gi, group in enumerate(root_groups):
        skills = grouped[group]
        is_last_group = gi == len(root_groups) - 1
        group_prefix = "└── " if is_last_group else "├── "
        branch = "    " if is_last_group else "│   "

        if len(skills) == 1 and skills[0].folder_name == group:
            skill = skills[0]
            sync_tag = "  [已同步]" if skill.sync else ""
            lines.append(f"{group_prefix}{group}/{sync_tag}  — {skill.summary}")
            continue

        lines.append(f"{group_prefix}{group}/")
        for si, skill in enumerate(skills):
            is_last_skill = si == len(skills) - 1
            skill_prefix = "└── " if is_last_skill else "├── "
            sync_tag = " [已同步]" if skill.sync else ""
            lines.append(f"{branch}{skill_prefix}{skill.folder_name}/{sync_tag}  — {skill.summary}")

    lines.append("```")
    return "\n".join(lines)


def update_readme(entries: list[SkillEntry]) -> bool:
    """更新 README.md 的 ## Skills 目录 部分。"""
    if not README_PATH.exists():
        return False

    grouped = group_entries(entries)
    synced_count = sum(1 for entry in entries if entry.sync)

    lines = [
        "## Skills 目录",
        "",
        "仓库内全部技能如下。带 `[已同步]` 的会安装到 `~/.claude/skills/`（在 `skills-sync.yaml` 的 `sync` 组）。",
        "",
        build_directory_tree(entries),
        "",
    ]

    for group in sorted(grouped.keys()):
        title = format_group_title(group)
        skills = grouped[group]
        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"`skills/{group}/`")
        lines.append("")
        for skill in skills:
            sync_badge = " `[已同步]`" if skill.sync else ""
            lines.append(
                f"- **[{skill.name}](./{skill.path}/SKILL.md)**{sync_badge} — {skill.summary}"
            )
        lines.append("")

    if synced_count == 0:
        lines.insert(
            3,
            "_当前无已同步技能。将技能 name 移到 `skills-sync.yaml` 的 `sync` 组后重新运行 `python3 scripts/skills-registry.py all`。_",
        )
        lines.insert(4, "")

    new_section = "\n".join(lines).rstrip() + "\n"
    content = README_PATH.read_text(encoding="utf-8")
    pattern = r"## Skills (?:列表|目录)\n.*?(?=\n## |\Z)"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_section, content, count=1, flags=re.DOTALL)
    else:
        if "## License" in content:
            content = content.replace("## License", new_section + "\n## License")
        else:
            content = content.rstrip() + "\n\n" + new_section

    content = content.replace(
        "注册表 `skills-registry.yaml` 按目录列出全部技能；要安装到 `~/.claude/skills/`，"
        "编辑 `skills-sync.yaml` 添加技能 `name`，再重新运行上述命令。",
        "编辑 `skills-sync.yaml`，在 `sync` / `unsync` 两组之间移动技能 `name`，再重新运行上述命令。",
    )
    README_PATH.write_text(content, encoding="utf-8")
    return True


def print_summary(entries: list[SkillEntry], changes: dict, sync_result: dict | None = None) -> None:
    """打印操作摘要。"""
    synced = sum(1 for entry in entries if entry.sync)
    print(f"\n📋 技能: {len(entries)} 个，{synced} 个在 sync 组")
    print(f"   配置: {SYNC_PATH}")

    if changes.get("new_skills"):
        print(f"\n➕ 新技能（已加入 unsync）: {', '.join(changes['new_skills'])}")
    if changes.get("removed_skills"):
        print(f"\n➖ 已移除: {', '.join(changes['removed_skills'])}")
    if changes.get("moved_to_sync"):
        print(f"\n📤 移到 sync: {', '.join(changes['moved_to_sync'])}")
    if changes.get("moved_to_unsync"):
        print(f"\n📥 移到 unsync: {', '.join(changes['moved_to_unsync'])}")

    if sync_result:
        if sync_result["removed"]:
            print(f"\n🗑️  已移除软链接: {', '.join(sync_result['removed'])}")
        if sync_result["linked"]:
            print(f"\n🔗 已链接: {', '.join(sync_result['linked'])}")
        if sync_result["skipped"]:
            print(f"\n⚠️  跳过: {', '.join(sync_result['skipped'])}")


def cmd_scan() -> list[SkillEntry]:
    """执行扫描并更新 skills-sync.yaml。"""
    entries, changes = scan_skills(reconcile=True)
    print_summary(entries, changes)
    return entries


def cmd_sync(entries: list[SkillEntry] | None = None) -> None:
    """执行 Claude Code 软链接同步。"""
    if entries is None:
        entries, _ = scan_skills(reconcile=False)
    result = sync_to_claude(entries)
    print_summary(entries, {}, result)


def cmd_readme(entries: list[SkillEntry] | None = None) -> None:
    """更新 README.md。"""
    if entries is None:
        entries, _ = scan_skills(reconcile=False)
    update_readme(entries)
    print(f"✅ 已更新 {README_PATH}")


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="管理 qi_Skills 技能配置与 Claude Code 同步")
    parser.add_argument(
        "command",
        choices=["scan", "sync", "readme", "all"],
        help="scan=更新skills-sync.yaml, sync=软链接同步, readme=更新README, all=全部执行",
    )
    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan()
    elif args.command == "sync":
        cmd_sync()
    elif args.command == "readme":
        cmd_readme()
    elif args.command == "all":
        entries, changes = scan_skills(reconcile=True)
        update_readme(entries)
        sync_result = sync_to_claude(entries)
        print_summary(entries, changes, sync_result)
        print(f"\n✅ 已更新 {README_PATH}")


if __name__ == "__main__":
    main()
