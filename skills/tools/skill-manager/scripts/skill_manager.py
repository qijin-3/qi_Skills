#!/usr/bin/env python3
"""
技能管理器：多设备配置、GitHub 仓库同步、软链接维护。

用法:
  python3 skill_manager.py [--device ID] <command> [args...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

SKILL_DIR = Path(__file__).resolve().parent.parent
SM_ROOT = Path(
    os.environ.get("SKILL_MANAGER_ROOT", os.environ.get("MYSKILLS_ROOT", "~/Skill Manager"))
).expanduser()
SKILLS_DIR = SM_ROOT / "Skills"
AGENT_SKILLS = Path(os.environ.get("AGENT_SKILLS", "~/.agent/skills")).expanduser()
CONFIGS_DIR = SM_ROOT / "configs"
CACHE_ROOT = SM_ROOT / ".cache" / "repos"
DEVICES_FILE = CONFIGS_DIR / "devices.json"
ACTIVE_DEVICE_FILE = SM_ROOT / ".active-device"
LAUNCHER_HTML = SM_ROOT / "Open Skill Manager.html"
LAUNCHER_CMD = SM_ROOT / "Open Skill Manager.command"

EXCLUDE_PARTS = {".git", "node_modules", "deprecated", "template", ".cache", "__pycache__"}


@dataclass
class DiscoveredSkill:
    """仓库内扫描到的技能。"""

    name: str
    source_path: str
    description: str
    summary: str


@dataclass
class Manager:
    """技能管理器上下文，持有当前设备配置。"""

    device_id: str
    manifest_path: Path
    data: dict = field(default_factory=dict)

    def save(self) -> None:
        """将当前设备配置写回磁盘。"""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["device_id"] = self.device_id
        self.manifest_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def parse_frontmatter(skill_md: Path) -> tuple[str, str]:
    """
    从 SKILL.md 提取 name 和 description。

    Returns:
        (name, description)；解析失败时 name 回退为目录名。
    """
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return skill_md.parent.name, ""

    block = match.group(1)
    if yaml is not None:
        meta = yaml.safe_load(block) or {}
        name = str(meta.get("name") or skill_md.parent.name).strip()
        desc = meta.get("description", "")
    else:
        name_m = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
        name = name_m.group(1).strip().strip("'\"") if name_m else skill_md.parent.name
        desc_m = re.search(r"^description:\s*(.+)$", block, re.MULTILINE | re.DOTALL)
        desc = desc_m.group(1).strip() if desc_m else ""

    if isinstance(desc, list):
        description = " ".join(str(line).strip() for line in desc).strip()
    else:
        description = str(desc).strip()
    description = re.sub(r"\s+", " ", description)
    return name, description


def summarize_description(description: str, max_len: int = 60) -> str:
    """将 description 压缩为摘要。"""
    text = description.strip()
    if not text:
        return ""
    for sep in ["。", ". ", "，", " — ", " - "]:
        if sep in text:
            text = text.split(sep, 1)[0].strip()
            break
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def sanitize_device_id(raw: str) -> str:
    """将 hostname 等字符串规范为 device-id。"""
    s = raw.lower().strip()
    s = re.sub(r"\.local$", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "default"


def parse_github_url(url: str) -> tuple[str, str]:
    """
    解析 GitHub 仓库 URL 或 owner/repo 简写。

    Returns:
        (repo_id, clone_url) 如 ("jin-dev/qi_Skills", "https://github.com/...")
    """
    url = url.strip().rstrip("/")
    if re.match(r"^[\w.-]+/[\w.-]+$", url):
        owner, repo = url.split("/", 1)
        repo = repo.removesuffix(".git")
        return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}.git"

    if url.startswith("git@"):
        m = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url)
        if not m:
            raise ValueError(f"无法解析 Git URL: {url}")
        owner, repo = m.group(1), m.group(2)
        return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}.git"

    parsed = urlparse(url)
    if "github.com" not in parsed.netloc:
        raise ValueError(f"仅支持 GitHub 仓库: {url}")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"无法解析 GitHub URL: {url}")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}.git"


def now_iso() -> str:
    """返回本地时区时间字符串 YYYY-MM-DD HH:MM。"""
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")


def git_commit_time(repo_path: Path, commit: str | None = None) -> str | None:
    """从 git 读取 commit 时间。"""
    if not (repo_path / ".git").exists():
        return None
    try:
        args = ["log", "-1", "--format=%ci"]
        if commit and commit not in ("local", ""):
            args.append(commit)
        raw = run_git(args, cwd=repo_path)
        return raw[:16]
    except RuntimeError:
        return None


def repo_updated_at(repo: dict) -> str | None:
    """返回仓库上次更新时间（manifest 优先，否则 git）。"""
    if repo.get("last_updated_at"):
        return repo["last_updated_at"]
    cache = repo_cache_path(repo)
    return git_commit_time(cache, repo.get("last_commit"))


def touch_repo_updated(repo: dict) -> None:
    """标记仓库更新时间。"""
    repo["last_updated_at"] = now_iso()


def cache_dir_for(repo_id: str) -> Path:
    """返回仓库 git 缓存目录路径。"""
    return CACHE_ROOT / repo_id.replace("/", "-")


def run_git(args: list[str], cwd: Path | None = None) -> str:
    """执行 git 命令并返回 stdout。"""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} 失败: {err}")
    return result.stdout.strip()


def git_head(repo_path: Path) -> str:
    """返回仓库当前 HEAD commit SHA；非 git 目录时返回 local。"""
    if not (repo_path / ".git").exists():
        return "local"
    try:
        return run_git(["rev-parse", "HEAD"], cwd=repo_path)
    except RuntimeError:
        return "local"


def git_fetch(repo_path: Path, branch: str) -> str:
    """fetch 远程分支并返回 origin/<branch> 的 commit SHA。"""
    run_git(["fetch", "origin", branch, "--depth", "1"], cwd=repo_path)
    return run_git(["rev-parse", f"origin/{branch}"], cwd=repo_path)


def clone_repo(url: str, branch: str, dest: Path) -> None:
    """浅克隆仓库到目标目录。"""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--depth", "1", "--branch", branch, url, str(dest)])


def load_devices_registry() -> dict:
    """加载 devices.json，不存在则返回空结构。"""
    if not DEVICES_FILE.exists():
        return {"version": 1, "devices": []}
    return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))


def list_device_configs() -> list[str]:
    """列出 configs/ 下所有设备配置文件 ID。"""
    if not CONFIGS_DIR.exists():
        return []
    return sorted(
        p.stem for p in CONFIGS_DIR.glob("*.json") if p.name != "devices.json"
    )


def resolve_device_id(override: str | None = None) -> str:
    """
    解析当前设备 ID。

    优先级：CLI override → 环境变量 → .active-device → devices.json hostname → sanitize(hostname)
    """
    if override:
        return override
    env = os.environ.get("SKILL_MANAGER_DEVICE", "").strip()
    if env:
        return env
    if ACTIVE_DEVICE_FILE.exists():
        active = ACTIVE_DEVICE_FILE.read_text(encoding="utf-8").strip()
        if active:
            return active

    hostname = socket.gethostname()
    registry = load_devices_registry()
    for dev in registry.get("devices", []):
        hostnames = [h.lower() for h in dev.get("hostnames", [])]
        if hostname.lower() in hostnames or sanitize_device_id(hostname) == dev.get("id", ""):
            return dev["id"]

    return sanitize_device_id(hostname)


def manifest_path_for(device_id: str) -> Path:
    """返回设备配置文件路径。"""
    return CONFIGS_DIR / f"{device_id}.json"


def ensure_workspace() -> None:
    """初始化 Skill Manager 工作区目录并部署启动器文件。"""
    SM_ROOT.mkdir(parents=True, exist_ok=True)
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_SKILLS.mkdir(parents=True, exist_ok=True)
    deploy_launcher_files()


def deploy_launcher_files() -> None:
    """将 HTML 启动器与 Mac .command 脚本部署到 Skill Manager 根目录。"""
    src_html = SKILL_DIR / "web" / "launcher.html"
    if src_html.exists():
        shutil.copy2(src_html, LAUNCHER_HTML)

    if sys.platform == "darwin":
        script = SKILL_DIR / "scripts" / "skill_manager.py"
        LAUNCHER_CMD.write_text(
            f"#!/bin/bash\n"
            f'cd "{SM_ROOT}"\n'
            f'exec python3 "{script}" ui\n',
            encoding="utf-8",
        )
        LAUNCHER_CMD.chmod(0o755)


def load_manager(device_id: str | None = None) -> Manager:
    """加载或初始化当前设备的管理器。"""
    ensure_workspace()
    did = resolve_device_id(device_id)
    path = manifest_path_for(did)

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "device_id": did, "repos": []}
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return Manager(device_id=did, manifest_path=path, data=data)


def set_active_device(device_id: str) -> None:
    """持久化当前活跃设备（GUI 切换用）。"""
    ensure_workspace()
    ACTIVE_DEVICE_FILE.write_text(device_id + "\n", encoding="utf-8")


def find_repo(mgr: Manager, repo_id: str) -> dict | None:
    """在配置中查找仓库记录。"""
    for repo in mgr.data.get("repos", []):
        if repo.get("id") == repo_id:
            return repo
    return None


def repo_cache_path(repo: dict) -> Path:
    """返回仓库缓存的绝对路径。"""
    rel = repo.get("cache_path", "")
    if rel:
        return SM_ROOT / rel
    return cache_dir_for(repo["id"])


def discover_skills_in_repo(repo_path: Path) -> list[DiscoveredSkill]:
    """递归扫描仓库内所有 SKILL.md。"""
    results: list[DiscoveredSkill] = []
    if not repo_path.is_dir():
        return results

    for skill_md in sorted(repo_path.rglob("SKILL.md")):
        rel = skill_md.relative_to(repo_path)
        if any(part in EXCLUDE_PARTS or part.startswith(".") for part in rel.parts[:-1]):
            continue
        name, description = parse_frontmatter(skill_md)
        source_path = skill_md.parent.relative_to(repo_path).as_posix()
        results.append(
            DiscoveredSkill(
                name=name,
                source_path=source_path,
                description=description,
                summary=summarize_description(description),
            )
        )
    results.sort(key=lambda s: s.name)
    return results


def skill_dest(name: str) -> Path:
    """本地技能安装目录（Skill Manager/Skills/<name>）。"""
    return SKILLS_DIR / name


def skill_link(name: str) -> Path:
    """~/.agent/skills 下的软链接路径。"""
    return AGENT_SKILLS / name


def find_skill_owner(mgr: Manager, skill_name: str) -> tuple[dict, dict] | None:
    """查找技能所属的仓库与记录。"""
    for repo in mgr.data.get("repos", []):
        for sk in repo.get("skills", []):
            if sk.get("name") == skill_name:
                return repo, sk
    return None


def check_name_conflict(mgr: Manager, skill_name: str, repo_id: str) -> str | None:
    """检查技能名是否已被其他仓库占用。"""
    for repo in mgr.data.get("repos", []):
        if repo.get("id") == repo_id:
            continue
        for sk in repo.get("skills", []):
            if sk.get("name") == skill_name and sk.get("sync"):
                return repo.get("id", "?")
    if skill_dest(skill_name).exists():
        owner = find_skill_owner(mgr, skill_name)
        if owner and owner[0].get("id") != repo_id:
            return owner[0].get("id", "?")
    return None


def copy_skill_tree(src: Path, dest: Path) -> None:
    """覆盖复制技能目录到本地。"""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def create_symlink(name: str) -> None:
    """创建 ~/.agent/skills/<name> -> Skill Manager/Skills/<name> 软链。"""
    dest = skill_dest(name)
    link = skill_link(name)
    if not dest.exists():
        raise FileNotFoundError(f"技能目录不存在: {dest}")
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(dest)


def remove_symlink(name: str) -> None:
    """移除软链接（若存在）。"""
    link = skill_link(name)
    if link.is_symlink() or link.is_file():
        link.unlink()
    elif link.is_dir() and not link.is_symlink():
        raise RuntimeError(f"{link} 是真实目录而非软链，请手动处理")


def healthcheck() -> dict:
    """
    扫描 ~/.agent/skills，删除断裂软链。

    Returns:
        报告字典：removed, broken, orphans
    """
    AGENT_SKILLS.mkdir(parents=True, exist_ok=True)
    removed: list[str] = []
    broken: list[str] = []

    for entry in AGENT_SKILLS.iterdir():
        if not entry.is_symlink():
            continue
        if not entry.resolve().exists():
            broken.append(entry.name)
            entry.unlink()
            removed.append(entry.name)

    orphans: list[str] = []
    if SKILLS_DIR.is_dir():
        linked_names = {
            p.name
            for p in AGENT_SKILLS.iterdir()
            if p.is_symlink() and p.resolve().exists()
        }
        for child in SKILLS_DIR.iterdir():
            if child.is_dir() and child.name not in linked_names:
                orphans.append(child.name)

    return {"removed": removed, "broken": broken, "orphans": orphans}


def repo_add(mgr: Manager, url: str, branch: str = "main") -> dict:
    """添加 GitHub 仓库并克隆到缓存。"""
    repo_id, clone_url = parse_github_url(url)
    if find_repo(mgr, repo_id):
        raise ValueError(f"仓库已存在: {repo_id}")

    cache = cache_dir_for(repo_id)
    clone_repo(clone_url, branch, cache)
    commit = git_head(cache)

    repo_entry = {
        "id": repo_id,
        "url": clone_url,
        "branch": branch,
        "cache_path": cache.relative_to(SM_ROOT).as_posix(),
        "last_commit": commit,
        "last_updated_at": git_commit_time(cache, commit) or now_iso(),
        "skills": [],
    }
    mgr.data.setdefault("repos", []).append(repo_entry)
    mgr.save()
    return repo_entry


def repo_remove(mgr: Manager, repo_id: str, purge: bool = False) -> dict:
    """移除仓库记录，可选卸载其下所有已同步技能。"""
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")

    uninstalled: list[str] = []
    if purge:
        for sk in list(repo.get("skills", [])):
            if sk.get("sync"):
                uninstall_skill(mgr, sk["name"], save=False)
                uninstalled.append(sk["name"])

    mgr.data["repos"] = [r for r in mgr.data["repos"] if r.get("id") != repo_id]
    mgr.save()
    return {"removed": repo_id, "uninstalled": uninstalled}


def repo_update_branch(mgr: Manager, repo_id: str, branch: str) -> dict:
    """修改仓库分支并重新 clone。"""
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")
    repo["branch"] = branch
    cache = repo_cache_path(repo)
    if cache.exists():
        shutil.rmtree(cache)
    clone_repo(repo["url"], branch, cache)
    repo["last_commit"] = git_head(cache)
    repo["last_updated_at"] = git_commit_time(cache, repo["last_commit"]) or now_iso()
    repo["cache_path"] = cache.relative_to(SM_ROOT).as_posix()
    mgr.save()
    return repo


def discover_repo(mgr: Manager, repo_id: str) -> list[dict]:
    """扫描仓库内技能，合并 manifest 中的 sync 状态。"""
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")

    cache = repo_cache_path(repo)
    if not cache.exists():
        clone_repo(repo["url"], repo.get("branch", "main"), cache)

    synced = {sk["name"]: sk for sk in repo.get("skills", [])}
    repo_time = repo_updated_at(repo)
    result = []
    for sk in discover_skills_in_repo(cache):
        existing = synced.get(sk.name)
        link = skill_link(sk.name)
        link_ok = link.is_symlink() and link.resolve().exists()
        installed_at = None
        if existing and existing.get("sync"):
            installed_at = existing.get("installed_at")
            if not installed_at and existing.get("installed_commit"):
                installed_at = git_commit_time(cache, existing["installed_commit"])
        result.append({
            "name": sk.name,
            "source_path": sk.source_path,
            "description": sk.description,
            "summary": sk.summary,
            "sync": bool(existing and existing.get("sync")),
            "installed_commit": existing.get("installed_commit") if existing else None,
            "installed_at": installed_at,
            "repo_updated_at": repo_time,
            "link_ok": link_ok,
        })
    return result


def install_skill(
    mgr: Manager,
    repo_id: str,
    skill_ref: str,
    *,
    save: bool = True,
) -> dict:
    """
    安装技能：从仓库缓存复制到 Skill Manager/Skills 并创建软链。

    skill_ref 可以是技能 name 或 source_path。
    """
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")

    cache = repo_cache_path(repo)
    if not cache.exists():
        clone_repo(repo["url"], repo.get("branch", "main"), cache)

    discovered = {sk.name: sk for sk in discover_skills_in_repo(cache)}
    by_path = {sk.source_path: sk for sk in discovered.values()}

    sk = discovered.get(skill_ref) or by_path.get(skill_ref)
    if not sk:
        raise ValueError(f"未找到技能: {skill_ref}")

    conflict = check_name_conflict(mgr, sk.name, repo_id)
    if conflict:
        raise ValueError(f"技能名 '{sk.name}' 已被仓库 {conflict} 占用")

    src = cache / sk.source_path
    copy_skill_tree(src, skill_dest(sk.name))
    create_symlink(sk.name)

    commit = git_head(cache)
    skills_list = repo.setdefault("skills", [])
    entry = next((s for s in skills_list if s.get("name") == sk.name), None)
    if entry is None:
        entry = {"name": sk.name, "source_path": sk.source_path}
        skills_list.append(entry)
    entry["source_path"] = sk.source_path
    entry["installed_commit"] = commit
    entry["installed_at"] = now_iso()
    entry["sync"] = True
    repo["last_commit"] = commit
    touch_repo_updated(repo)

    if save:
        mgr.save()
    return {"name": sk.name, "source_path": sk.source_path, "commit": commit}


def uninstall_skill(mgr: Manager, skill_name: str, *, save: bool = True) -> dict:
    """卸载技能：删除本地副本、软链和 manifest 记录。"""
    dest = skill_dest(skill_name)
    if dest.exists():
        shutil.rmtree(dest)
    remove_symlink(skill_name)

    for repo in mgr.data.get("repos", []):
        repo["skills"] = [s for s in repo.get("skills", []) if s.get("name") != skill_name]

    if save:
        mgr.save()
    return {"uninstalled": skill_name}


def update_skills(
    mgr: Manager,
    repo_id: str | None = None,
    skill_name: str | None = None,
) -> list[dict]:
    """检查并覆盖更新有变化的已同步技能。"""
    updated: list[dict] = []

    for repo in mgr.data.get("repos", []):
        if repo_id and repo.get("id") != repo_id:
            continue

        cache = repo_cache_path(repo)
        if not cache.exists():
            clone_repo(repo["url"], repo.get("branch", "main"), cache)

        branch = repo.get("branch", "main")
        try:
            remote_commit = git_fetch(cache, branch)
        except RuntimeError:
            remote_commit = git_head(cache)

        local_commit = repo.get("last_commit", "")
        if remote_commit == local_commit and not skill_name:
            continue

        repo["last_commit"] = remote_commit
        touch_repo_updated(repo)

        for sk in repo.get("skills", []):
            if not sk.get("sync"):
                continue
            if skill_name and sk.get("name") != skill_name:
                continue
            if sk.get("installed_commit") == remote_commit and not skill_name:
                continue

            src = cache / sk["source_path"]
            if not src.exists():
                continue

            copy_skill_tree(src, skill_dest(sk["name"]))
            create_symlink(sk["name"])
            sk["installed_commit"] = remote_commit
            sk["installed_at"] = now_iso()
            updated.append({
                "name": sk["name"],
                "repo": repo["id"],
                "commit": remote_commit,
            })

    mgr.save()
    return updated


def skill_diff_summary(
    cache: Path,
    source_path: str,
    old_commit: str | None,
    new_commit: str,
) -> str:
    """生成技能目录在两次 commit 之间的 diff 摘要。"""
    if not old_commit or old_commit in ("local", "") or old_commit == new_commit:
        return "云端有新版本"
    try:
        stat = run_git(
            ["diff", "--stat", old_commit, new_commit, "--", source_path],
            cwd=cache,
        )
        lines = [ln.strip() for ln in stat.strip().splitlines() if ln.strip()]
        if not lines:
            return "commit 已变化，该技能路径无文件差异"
        return lines[-1][:120]
    except RuntimeError:
        return f"{old_commit[:8]} → {new_commit[:8]}"


def check_updates(mgr: Manager) -> dict:
    """
    检查云端仓库与本地已同步技能的差异（仅 fetch，不覆盖本地）。

    Returns:
        {"checked_at": "...", "updates": [...]}
    """
    updates: list[dict] = []

    for repo in mgr.data.get("repos", []):
        cache = repo_cache_path(repo)
        if not cache.exists():
            clone_repo(repo["url"], repo.get("branch", "main"), cache)

        branch = repo.get("branch", "main")
        try:
            remote_commit = git_fetch(cache, branch)
        except RuntimeError:
            remote_commit = git_head(cache)

        remote_time = git_commit_time(cache, remote_commit)

        for sk in repo.get("skills", []):
            if not sk.get("sync"):
                continue
            local_commit = sk.get("installed_commit") or ""
            if local_commit == remote_commit:
                continue

            src = cache / sk.get("source_path", "")
            if not src.exists():
                continue

            updates.append({
                "repo_id": repo["id"],
                "name": sk["name"],
                "source_path": sk.get("source_path", ""),
                "local_commit": local_commit[:8] if local_commit else "—",
                "remote_commit": remote_commit[:8],
                "local_updated_at": sk.get("installed_at"),
                "remote_updated_at": remote_time,
                "diff_summary": skill_diff_summary(
                    cache, sk.get("source_path", ""), local_commit, remote_commit
                ),
            })

    return {"checked_at": now_iso(), "updates": updates}


def apply_updates(mgr: Manager, items: list[dict]) -> list[dict]:
    """应用用户选中的技能更新（覆盖式）。"""
    updated: list[dict] = []
    for item in items:
        repo_id = item.get("repo_id", "")
        name = item.get("name", "")
        if not repo_id or not name:
            continue
        updated.extend(update_skills(mgr, repo_id, name))
    return updated


def sync_skills_batch(
    mgr: Manager,
    repo_id: str,
    skills: list[dict],
) -> dict:
    """
    批量更新某仓库的技能 sync 状态。

    skills: [{"name": "...", "sync": true/false}, ...]
    """
    installed: list[str] = []
    uninstalled: list[str] = []

    want = {s["name"]: s.get("sync", False) for s in skills}
    discovered = {s["name"]: s for s in discover_repo(mgr, repo_id)}

    for name, sync in want.items():
        if name not in discovered:
            continue
        if sync:
            install_skill(mgr, repo_id, name, save=False)
            installed.append(name)
        else:
            owner = find_skill_owner(mgr, name)
            if owner and owner[0].get("id") == repo_id:
                uninstall_skill(mgr, name, save=False)
                uninstalled.append(name)

    mgr.save()
    return {"installed": installed, "uninstalled": uninstalled}


def sync_skills_multi(mgr: Manager, actions: list[dict]) -> dict:
    """
    跨仓库批量同步技能。

    actions: [{"repo_id": "...", "name": "...", "sync": true/false}, ...]
    """
    by_repo: dict[str, list[dict]] = {}
    for act in actions:
        rid = act.get("repo_id", "")
        name = act.get("name", "")
        if not rid or not name:
            continue
        by_repo.setdefault(rid, []).append({"name": name, "sync": bool(act.get("sync"))})

    installed: list[str] = []
    uninstalled: list[str] = []
    for repo_id, skills in by_repo.items():
        result = sync_skills_batch(mgr, repo_id, skills)
        installed.extend(result.get("installed", []))
        uninstalled.extend(result.get("uninstalled", []))

    return {"installed": installed, "uninstalled": uninstalled}


def get_status(mgr: Manager) -> dict:
    """汇总当前设备状态。"""
    hc = healthcheck()
    repos_summary = []
    total_synced = 0

    for repo in mgr.data.get("repos", []):
        synced = [s for s in repo.get("skills", []) if s.get("sync")]
        total_synced += len(synced)
        repos_summary.append({
            "id": repo["id"],
            "branch": repo.get("branch", "main"),
            "last_commit": repo.get("last_commit", "")[:8],
            "synced_count": len(synced),
        })

    return {
        "device_id": mgr.device_id,
        "hostname": socket.gethostname(),
        "manifest_path": str(mgr.manifest_path),
        "repos": repos_summary,
        "total_synced": total_synced,
        "healthcheck": hc,
    }


def get_device_info(mgr: Manager) -> dict:
    """返回当前设备及可用设备列表。"""
    configs = list_device_configs()
    current = mgr.device_id
    if current not in configs:
        configs = sorted(set(configs + [current]))
    return {
        "current": {
            "device_id": current,
            "hostname": socket.gethostname(),
            "manifest_path": str(mgr.manifest_path),
        },
        "available": configs,
    }


# --- CLI -------------------------------------------------------------------

def cmd_healthcheck(_args: argparse.Namespace) -> int:
    """执行健康检查并打印结果。"""
    report = healthcheck()
    if report["removed"]:
        print(f"已移除断裂软链: {', '.join(report['removed'])}")
    else:
        print("软链健康，无断裂链接。")
    if report["orphans"]:
        print(f"孤儿目录（无软链）: {', '.join(report['orphans'])}")
    return 0


def cmd_device(args: argparse.Namespace) -> int:
    """设备相关子命令。"""
    if args.device_cmd == "list":
        configs = list_device_configs()
        registry = load_devices_registry()
        print("设备配置:")
        for cid in configs:
            mark = " *" if cid == resolve_device_id(args.device) else ""
            print(f"  {cid}{mark}")
        if registry.get("devices"):
            print("\ndevices.json 注册:")
            for d in registry["devices"]:
                print(f"  {d['id']}: {', '.join(d.get('hostnames', []))}")
        return 0

    mgr = load_manager(args.device)
    print(f"当前设备: {mgr.device_id}")
    print(f"配置文件: {mgr.manifest_path}")
    print(f"hostname: {socket.gethostname()}")
    return 0


def cmd_repo(args: argparse.Namespace) -> int:
    """仓库 CRUD。"""
    mgr = load_manager(args.device)

    if args.repo_cmd == "add":
        repo = repo_add(mgr, args.url, args.branch or "main")
        print(f"已添加: {repo['id']} @ {repo['last_commit'][:8]}")
        return 0

    if args.repo_cmd == "list":
        for repo in mgr.data.get("repos", []):
            synced = sum(1 for s in repo.get("skills", []) if s.get("sync"))
            print(f"{repo['id']}  branch={repo.get('branch')}  synced={synced}  commit={repo.get('last_commit', '')[:8]}")
        return 0

    if args.repo_cmd == "remove":
        result = repo_remove(mgr, args.repo_id, purge=args.purge)
        print(f"已移除仓库: {result['removed']}")
        if result["uninstalled"]:
            print(f"已卸载技能: {', '.join(result['uninstalled'])}")
        return 0

    return 1


def cmd_discover(args: argparse.Namespace) -> int:
    """扫描仓库技能。"""
    mgr = load_manager(args.device)
    skills = discover_repo(mgr, args.repo_id)
    for sk in skills:
        mark = "✓" if sk["sync"] else " "
        print(f"[{mark}] {sk['name']:30} {sk['source_path']:40} {sk['summary']}")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """安装技能。"""
    mgr = load_manager(args.device)
    result = install_skill(mgr, args.repo_id, args.skill)
    print(f"已安装: {result['name']} @ {result['commit'][:8]}")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    """卸载技能。"""
    mgr = load_manager(args.device)
    result = uninstall_skill(mgr, args.name)
    print(f"已卸载: {result['uninstalled']}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """应用技能更新（覆盖式）。"""
    mgr = load_manager(args.device)
    updated = update_skills(mgr, args.repo_id, args.skill)
    if not updated:
        print("所有技能已是最新。")
    else:
        for u in updated:
            print(f"已更新: {u['name']} ({u['repo']}) -> {u['commit'][:8]}")
    return 0


def cmd_check_updates(args: argparse.Namespace) -> int:
    """检查云端与本地差异，不自动更新。"""
    mgr = load_manager(args.device)
    result = check_updates(mgr)
    updates = result.get("updates", [])
    if not updates:
        print("所有已同步技能均与云端一致。")
        return 0
    print(f"发现 {len(updates)} 项可更新（{result.get('checked_at')}）:")
    for u in updates:
        print(f"  [{u['repo_id']}] {u['name']}: {u['local_commit']} → {u['remote_commit']}")
        print(f"    {u.get('diff_summary', '')}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """打印状态摘要。"""
    mgr = load_manager(args.device)
    st = get_status(mgr)
    print(f"设备: {st['device_id']} ({st['hostname']})")
    print(f"配置: {st['manifest_path']}")
    print(f"已同步技能: {st['total_synced']}")
    for repo in st["repos"]:
        print(f"  {repo['id']}: {repo['synced_count']} synced @ {repo['last_commit']}")
    hc = st["healthcheck"]
    if hc["removed"]:
        print(f"已清理断裂软链: {', '.join(hc['removed'])}")
    return 0


def cmd_init(_args: argparse.Namespace) -> int:
    """初始化 Skill Manager 工作区与启动器。"""
    ensure_workspace()
    mgr = load_manager(_args.device)
    print(f"工作区: {SM_ROOT}")
    print(f"技能目录: {SKILLS_DIR}")
    print(f"配置文件: {mgr.manifest_path}")
    print(f"启动器: {LAUNCHER_HTML}")
    if LAUNCHER_CMD.exists():
        print(f"快捷启动: {LAUNCHER_CMD}")
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    """启动 Web GUI。"""
    from serve import run_server  # noqa: WPS433

    port = args.port or int(os.environ.get("SM_PORT", "8791"))
    run_server(port=port, device_id=args.device, open_browser=not args.no_open)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(description="技能管理器")
    parser.add_argument("--device", help="覆盖当前设备 ID")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("healthcheck", help="清理断裂软链")
    sub.add_parser("init", help="初始化 Skill Manager 工作区")

    dev = sub.add_parser("device", help="设备管理")
    dev_sub = dev.add_subparsers(dest="device_cmd", required=True)
    dev_sub.add_parser("list", help="列出设备配置")
    dev_sub.add_parser("current", help="显示当前设备")

    repo = sub.add_parser("repo", help="仓库管理")
    repo_sub = repo.add_subparsers(dest="repo_cmd", required=True)
    ra = repo_sub.add_parser("add", help="添加仓库")
    ra.add_argument("url", help="GitHub URL 或 owner/repo")
    ra.add_argument("--branch", default="main")
    repo_sub.add_parser("list", help="列出仓库")
    rr = repo_sub.add_parser("remove", help="移除仓库")
    rr.add_argument("repo_id")
    rr.add_argument("--purge", action="store_true", help="同时卸载其下技能")

    disc = sub.add_parser("discover", help="扫描仓库技能")
    disc.add_argument("repo_id")

    inst = sub.add_parser("install", help="安装技能")
    inst.add_argument("repo_id")
    inst.add_argument("skill", help="技能 name 或 source_path")

    uninst = sub.add_parser("uninstall", help="卸载技能")
    uninst.add_argument("name")

    upd = sub.add_parser("update", help="应用技能更新（覆盖式）")
    upd.add_argument("--repo", dest="repo_id")
    upd.add_argument("--skill")

    sub.add_parser("check-updates", help="检查云端与本地差异")

    sub.add_parser("status", help="状态摘要")

    ui = sub.add_parser("ui", help="启动 Web GUI")
    ui.add_argument("--port", type=int)
    ui.add_argument("--no-open", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "healthcheck": cmd_healthcheck,
        "init": cmd_init,
        "device": cmd_device,
        "repo": cmd_repo,
        "discover": cmd_discover,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "update": cmd_update,
        "check-updates": cmd_check_updates,
        "status": cmd_status,
        "ui": cmd_ui,
    }
    handler = handlers.get(args.command)
    if not handler:
        parser.print_help()
        return 1
    try:
        return handler(args)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
