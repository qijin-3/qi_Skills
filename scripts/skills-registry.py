#!/usr/bin/env python3
"""
扫描 skills/ 目录并更新 README.md 技能目录。

用法:
  python scripts/skills-registry.py          # 更新 README.md（默认）
  python scripts/skills-registry.py readme   # 同上
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
README_PATH = REPO_ROOT / "README.md"

KNOWN_CATEGORIES = {"engineering", "productivity", "misc", "deprecated"}
EXCLUDE_PATH_PARTS = {"node_modules", "deprecated", "template"}

GROUP_TITLES = {
    "engineering": "Engineering",
    "productivity": "Productivity",
    "misc": "Misc",
    "product design": "Product Design",
    "travel_journal": "Travel Journal",
    "meeting": "Meeting",
    "personal_os": "Personal OS",
    "health_os": "Health OS",
}


@dataclass
class SkillEntry:
    """扫描到的单个技能条目。"""

    path: str
    name: str
    description: str
    summary: str
    group: str

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


def scan_skills() -> list[SkillEntry]:
    """扫描 skills/ 目录并返回技能列表。"""
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
    return entries


def extract_readme_skill_names(content: str) -> set[str]:
    """从 README 技能列表中提取已有技能 name。"""
    return set(re.findall(r"\*\*\[([^\]]+)\]\(\./skills/", content))


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
            lines.append(f"{group_prefix}{group}/  — {skill.summary}")
            continue

        lines.append(f"{group_prefix}{group}/")
        for si, skill in enumerate(skills):
            is_last_skill = si == len(skills) - 1
            skill_prefix = "└── " if is_last_skill else "├── "
            lines.append(f"{branch}{skill_prefix}{skill.folder_name}/  — {skill.summary}")

    lines.append("```")
    return "\n".join(lines)


def update_readme(entries: list[SkillEntry]) -> tuple[bool, dict]:
    """
    更新 README.md 的 ## Skills 目录 部分。

    Returns:
        (是否写入成功, 变更摘要)
    """
    if not README_PATH.exists():
        return False, {}

    old_content = README_PATH.read_text(encoding="utf-8")
    old_names = extract_readme_skill_names(old_content)
    new_names = {entry.name for entry in entries}
    changes = {
        "new_skills": sorted(new_names - old_names),
        "removed_skills": sorted(old_names - new_names),
    }

    grouped = group_entries(entries)
    lines = [
        "## Skills 目录",
        "",
        "仓库内全部技能如下。",
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
            lines.append(f"- **[{skill.name}](./{skill.path}/SKILL.md)** — {skill.summary}")
        lines.append("")

    new_section = "\n".join(lines).rstrip() + "\n"
    content = old_content
    pattern = r"## Skills (?:列表|目录)\n.*?(?=\n## |\Z)"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_section, content, count=1, flags=re.DOTALL)
    else:
        if "## License" in content:
            content = content.replace("## License", new_section + "\n## License")
        else:
            content = content.rstrip() + "\n\n" + new_section

    README_PATH.write_text(content, encoding="utf-8")
    return True, changes


def print_summary(entries: list[SkillEntry], changes: dict) -> None:
    """打印操作摘要。"""
    print(f"\n📋 技能: {len(entries)} 个")
    if changes.get("new_skills"):
        print(f"\n➕ 新技能: {', '.join(changes['new_skills'])}")
    if changes.get("removed_skills"):
        print(f"\n➖ 已移除: {', '.join(changes['removed_skills'])}")


def cmd_readme() -> None:
    """扫描 skills/ 并更新 README.md。"""
    entries = scan_skills()
    ok, changes = update_readme(entries)
    if not ok:
        print(f"error: 未找到 {README_PATH}", file=sys.stderr)
        raise SystemExit(1)
    print_summary(entries, changes)
    print(f"\n✅ 已更新 {README_PATH}")


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="扫描 skills/ 并更新 README.md")
    parser.add_argument(
        "command",
        nargs="?",
        default="readme",
        choices=["readme"],
        help="更新 README.md 技能目录（默认）",
    )
    args = parser.parse_args()
    if args.command == "readme":
        cmd_readme()


if __name__ == "__main__":
    main()
