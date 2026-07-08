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
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

SKILL_DIR = Path(__file__).resolve().parent.parent


def infer_sm_root_from_script() -> Path | None:
    """从 Local 安装路径反推 Skill Manager 根目录（换机复制后无需环境变量）。"""
    script = Path(__file__).resolve()
    parts = script.parts
    try:
        idx = parts.index("skill-manager")
    except ValueError:
        return None
    if idx < 3 or parts[idx - 1] != "local" or parts[idx - 2] != "Skills":
        return None
    cfg_dir = Path(*parts[: idx - 2])
    sm_root = cfg_dir.parent
    if (cfg_dir / "config.json").is_file():
        return sm_root
    return None


def resolve_sm_root() -> Path:
    """解析 Skill Manager 工作区根目录。"""
    for key in ("SKILL_MANAGER_ROOT", "MYSKILLS_ROOT"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser()
    inferred = infer_sm_root_from_script()
    if inferred is not None:
        return inferred
    return Path("~/Skill Manager").expanduser()


SM_ROOT = resolve_sm_root()
LEGACY_SKILLS_DIR = SM_ROOT / "Skills"
LEGACY_CONFIGS_DIR = SM_ROOT / "configs"
MIGRATED_DIR = SM_ROOT / ".migrated"
MIGRATED_CONFIGS_ARCHIVE = MIGRATED_DIR / "configs"
AGENT_SKILLS = Path(os.environ.get("AGENT_SKILLS", "~/.agents/skills")).expanduser()
CACHE_ROOT = SM_ROOT / ".cache" / "repos"
DEVICES_FILE = MIGRATED_DIR / "devices.json"
ACTIVE_DEVICE_FILE = SM_ROOT / ".active-device"
ACTIVE_CONFIG_FILE = SM_ROOT / ".active-config"
LAYOUT_MIGRATION_FLAG = SM_ROOT / ".layout-v2"
SM_RESERVED_NAMES = frozenset({
    ".cache", "configs", "Skills", "Open Skill Manager.command",
})
GUI_INDEX = SM_ROOT / "index.html"
LEGACY_LAUNCHER_HTML = SM_ROOT / "Open Skill Manager.html"
OBSOLETE_LAUNCHER_CMD = SM_ROOT / "Start Service.command"
LAUNCHER_CMD = SM_ROOT / "Open Skill Manager.command"
DEFAULT_UI_PORT = 8791
WATCHDOG_PORT = 8790
WATCHDOG_SCRIPT = SKILL_DIR / "scripts" / "watchdog.py"
SETTINGS_FILE = SM_ROOT / "settings.json"
SAMPLE_WEB_DIR = SKILL_DIR / "web"
SAMPLE_GUI_INDEX = SAMPLE_WEB_DIR / "index.sample.html"

DEFAULT_AGENTS: list[dict] = [
    {"id": "agents", "name": "Agents", "path": "~/.agents/skills", "enabled": True},
    {"id": "cursor", "name": "Cursor", "path": "~/.cursor/skills", "enabled": False},
    {"id": "claude", "name": "Claude Code", "path": "~/.claude/skills", "enabled": False},
    {"id": "codex", "name": "Codex", "path": "~/.codex/skills", "enabled": False},
    {"id": "antigravity", "name": "Antigravity", "path": "~/.gemini/config/skills", "enabled": False},
    {"id": "gemini", "name": "Gemini CLI", "path": "~/.gemini/skills", "enabled": False},
    {"id": "opencode", "name": "OpenCode", "path": "~/.config/opencode/skills", "enabled": False},
    {"id": "windsurf", "name": "Windsurf", "path": "~/.codeium/windsurf/skills", "enabled": False},
    {"id": "cline", "name": "Cline", "path": "~/.cline/skills", "enabled": False},
    {"id": "roo", "name": "Roo Code", "path": "~/.roo/skills", "enabled": False},
]
SETTINGS_VERSION = 5
LEGACY_AGENT_PATH = "~/.agent/skills"
LEGACY_AGENT_SKILLS = Path("~/.agent/skills").expanduser()
LEGACY_AGENT_ID = "agent"
MANAGER_LINK_NAME = "skill-manager"
REMOVED_AGENT_IDS = frozenset({"cursor-builtin", LEGACY_AGENT_ID})
DEFAULT_AGENT_IDS = {a["id"] for a in DEFAULT_AGENTS}

LOCAL_REPO_ID = "__local__"
MANIFEST_VERSION = 2

BUILTIN_REPOS: list[dict] = [
    {
        "id": "anthropics/skills",
        "url": "https://github.com/anthropics/skills.git",
        "branch": "main",
        "alias": "Anthropics",
    },
    {
        "id": LOCAL_REPO_ID,
        "alias": "Local",
        "local": True,
    },
]

EXCLUDE_PARTS = {".git", "node_modules", "deprecated", "template", ".cache", "__pycache__"}

# ponytail: 进程内只 bootstrap 一次，避免每个 API 请求重复写盘/拉 watchdog
_bootstrapped_devices: set[str] = set()
_bootstrap_lock = threading.Lock()
_watchdog_lock = threading.Lock()


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
        """将当前设备配置写回磁盘（原子写入，避免并发截断）。"""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["device_id"] = self.device_id
        payload = json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"
        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.manifest_path)


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
    """
    fetch 远程分支并同步工作区到最新 commit。

    ponytail: 浅克隆 fetch 后 HEAD 不会自动前进，复制文件前必须 reset。
    """
    run_git(["fetch", "origin", branch, "--depth", "1"], cwd=repo_path)
    commit = run_git(["rev-parse", f"origin/{branch}"], cwd=repo_path)
    run_git(["reset", "--hard", commit], cwd=repo_path)
    return commit


def clone_repo(url: str, branch: str, dest: Path) -> None:
    """浅克隆仓库到目标目录。"""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--depth", "1", "--branch", branch, url, str(dest)])


def load_devices_registry() -> dict:
    """加载 devices.json（优先 .migrated，兼容旧 configs/ 路径）。"""
    if DEVICES_FILE.exists():
        return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))
    legacy_devices = LEGACY_CONFIGS_DIR / "devices.json"
    if legacy_devices.exists():
        MIGRATED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_devices, DEVICES_FILE)
        return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))
    return {"version": 1, "devices": []}


def list_device_configs() -> list[str]:
    """列出所有配置 ID（新布局目录 + 旧 configs/）。"""
    ids: set[str] = set()
    if SM_ROOT.is_dir():
        for p in SM_ROOT.iterdir():
            if not p.is_dir() or p.name.startswith("."):
                continue
            if p.name in SM_RESERVED_NAMES:
                continue
            if (p / "config.json").is_file():
                ids.add(p.name)
    if LEGACY_CONFIGS_DIR.exists():
        for p in LEGACY_CONFIGS_DIR.glob("*.json"):
            if p.name != "devices.json":
                ids.add(p.stem)
    return sorted(ids)


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
    if ACTIVE_CONFIG_FILE.exists():
        active = ACTIVE_CONFIG_FILE.read_text(encoding="utf-8").strip()
        if active:
            return active
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


def merge_agent_settings(saved_agents: list[dict], *, reset_enabled: bool = False) -> list[dict]:
    """将已保存配置与默认 Agent 列表合并（默认项优先、保留用户自定义路径）。"""
    by_id = {a["id"]: a for a in saved_agents if a.get("id")}
    merged: list[dict] = []
    for default in DEFAULT_AGENTS:
        aid = default["id"]
        saved = by_id.get(aid, {})
        if not saved and aid == "agents":
            saved = by_id.get(LEGACY_AGENT_ID, {})
        if reset_enabled or aid not in by_id:
            enabled = default.get("enabled", False)
        else:
            enabled = saved.get("enabled", default.get("enabled", False))
        path = str(saved.get("path") or default["path"]).strip()
        if aid in ("agents", LEGACY_AGENT_ID) and path in (LEGACY_AGENT_PATH, "~/.agent/skills"):
            path = "~/.agents/skills"
        merged.append({
            "id": aid,
            "name": str(saved.get("name") or default["name"]).strip(),
            "path": path,
            "enabled": enabled,
        })
    for agent in saved_agents:
        aid = agent.get("id", "")
        if aid and aid not in DEFAULT_AGENT_IDS and aid not in REMOVED_AGENT_IDS:
            merged.append(agent)
    return merged


def migrate_settings(data: dict) -> bool:
    """迁移旧版设置（路径修正、移除重复项）。"""
    changed = False
    version = data.get("version", 1)
    agents = data.get("agents", [])

    if version < SETTINGS_VERSION:
        for agent in agents:
            if agent.get("id") == LEGACY_AGENT_ID:
                agent["id"] = "agents"
                changed = True
            if agent.get("id") == "agents":
                if agent.get("path") in (LEGACY_AGENT_PATH, "~/.agent/skills"):
                    agent["path"] = "~/.agents/skills"
                    changed = True
                if agent.get("name") == "Agent":
                    agent["name"] = "Agents"
                    changed = True
        # 移除已废弃的 Agent 项（含旧 id agent，已合并为 agents）
        before = len(agents)
        data["agents"] = [
            a for a in agents
            if a.get("id") not in REMOVED_AGENT_IDS
        ]
        if len(data["agents"]) < before:
            changed = True
        data["version"] = SETTINGS_VERSION
        changed = True

    return changed


def migrate_legacy_symlinks() -> dict:
    """
    将 ~/.agent/skills 下指向 Skill Manager 的技能软链迁移到 ~/.agents/skills。

    保留 ~/.agent/skills/skill-manager（管理器 CLI 入口）。
    """
    legacy = LEGACY_AGENT_SKILLS
    target = AGENT_SKILLS
    if not legacy.is_dir():
        return {"moved": [], "skipped": []}

    target.mkdir(parents=True, exist_ok=True)
    cid = resolve_device_id()
    if manifest_path_for(cid).exists():
        skills_root = (config_dir(cid) / "Skills").resolve()
    else:
        skills_root = LEGACY_SKILLS_DIR.resolve()
    moved: list[str] = []
    skipped: list[str] = []

    for entry in legacy.iterdir():
        name = entry.name
        if name.startswith(".") or name == MANAGER_LINK_NAME:
            continue
        if not entry.is_symlink():
            skipped.append(name)
            continue
        try:
            dest = entry.resolve()
        except (OSError, RuntimeError):
            skipped.append(name)
            continue
        try:
            dest.relative_to(skills_root)
        except ValueError:
            skipped.append(name)
            continue

        new_link = target / name
        if new_link.exists():
            if new_link.is_symlink() and new_link.resolve() == dest:
                entry.unlink()
                moved.append(name)
            else:
                skipped.append(name)
            continue
        new_link.symlink_to(dest)
        entry.unlink()
        moved.append(name)

    return {"moved": moved, "skipped": skipped}


def load_settings() -> dict:
    """加载全局设置（Agent 技能目录等）。"""
    if not SETTINGS_FILE.exists():
        data = {"version": SETTINGS_VERSION, "agents": [dict(a) for a in DEFAULT_AGENTS]}
        save_settings(data)
        return data
    data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    if data.get("agents"):
        reset = data.get("version", 1) < 2
        if migrate_settings(data):
            save_settings(data)
        data["agents"] = merge_agent_settings(data["agents"], reset_enabled=reset)
        if reset:
            data["version"] = SETTINGS_VERSION
            save_settings(data)
        return data
    return {"version": SETTINGS_VERSION, "agents": [dict(a) for a in DEFAULT_AGENTS]}


def save_settings(data: dict) -> None:
    """保存全局设置到磁盘。"""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_enabled_agent_paths() -> list[Path]:
    """返回已启用的 Agent 技能目录列表。"""
    paths: list[Path] = []
    for agent in load_settings().get("agents", []):
        if not agent.get("enabled", True):
            continue
        raw = str(agent.get("path", "")).strip()
        if raw:
            paths.append(Path(raw).expanduser())
    if not paths:
        paths.append(AGENT_SKILLS)
    return paths


def count_skills_in_dir(path: Path) -> int:
    """统计目录下的技能数量（顶层目录或软链，忽略隐藏项）。"""
    if not path.is_dir():
        return 0
    return sum(
        1
        for p in path.iterdir()
        if not p.name.startswith(".") and (p.is_symlink() or p.is_dir())
    )


def get_settings_info() -> dict:
    """返回设置与各 Agent 技能数量。"""
    settings = load_settings()
    agents: list[dict] = []
    for i, agent in enumerate(settings.get("agents", [])):
        path = Path(str(agent.get("path", ""))).expanduser()
        agents.append({
            "id": agent.get("id", ""),
            "name": agent.get("name", ""),
            "path": str(agent.get("path", "")),
            "enabled": bool(agent.get("enabled", True)),
            "is_default": i == 0,
            "exists": path.is_dir(),
            "skill_count": count_skills_in_dir(path),
            "resolved_path": str(path),
        })
    return {"settings": settings, "agents": agents}


def open_agent_path(path_str: str) -> str:
    """在 Finder 中打开 Agent 技能目录（不存在则创建）。"""
    raw = path_str.strip()
    if not raw:
        raise ValueError("路径不能为空")
    path = Path(raw).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform != "darwin":
        raise RuntimeError("打开目录仅支持 macOS")
    subprocess.run(["open", str(path)], check=True)
    return str(path)


def update_settings(agents: list[dict]) -> dict:
    """更新 Agent 路径配置。"""
    cleaned: list[dict] = []
    seen: set[str] = set()
    for agent in agents:
        aid = str(agent.get("id", "")).strip() or f"agents-{len(cleaned)}"
        if aid in seen:
            continue
        seen.add(aid)
        path = str(agent.get("path", "")).strip()
        if not path:
            continue
        cleaned.append({
            "id": aid,
            "name": str(agent.get("name", aid)).strip() or aid,
            "path": path,
            "enabled": bool(agent.get("enabled", True)),
        })
    if not cleaned:
        raise ValueError("至少保留一个 Agent 配置")
    data = {"version": SETTINGS_VERSION, "agents": cleaned}
    save_settings(data)
    return get_settings_info()


def repo_slug(repo_id: str) -> str:
    """将仓库 id 转为 Skills 子目录名。"""
    if repo_id == LOCAL_REPO_ID:
        return "local"
    return repo_id.replace("/", "-")


def config_dir(config_id: str) -> Path:
    """返回某配置的根目录（含 config.json 与 Skills）。"""
    return SM_ROOT / config_id


def manifest_path_for(config_id: str) -> Path:
    """返回配置文件路径（新布局：{配置名}/config.json）。"""
    return config_dir(config_id) / "config.json"


def legacy_manifest_path(config_id: str) -> Path:
    """旧版 configs/{id}.json 路径（只读，目录可能已移除）。"""
    return LEGACY_CONFIGS_DIR / f"{config_id}.json"


def _consolidate_legacy_configs_archive() -> None:
    """将 configs/.migrated 归档并入 .migrated/configs/。"""
    old_archive = LEGACY_CONFIGS_DIR / ".migrated"
    if not old_archive.is_dir():
        return
    MIGRATED_CONFIGS_ARCHIVE.mkdir(parents=True, exist_ok=True)
    for item in old_archive.iterdir():
        dest = MIGRATED_CONFIGS_ARCHIVE / item.name
        if item.is_file() and not dest.exists():
            shutil.move(str(item), str(dest))
        elif item.is_file():
            item.unlink(missing_ok=True)
    try:
        old_archive.rmdir()
    except OSError:
        pass


def remove_legacy_configs_dir() -> None:
    """legacy configs/ 内容归档后删除该目录。"""
    if not LEGACY_CONFIGS_DIR.is_dir():
        return
    _consolidate_legacy_configs_archive()
    try:
        shutil.rmtree(LEGACY_CONFIGS_DIR)
    except OSError:
        pass


def archive_legacy_manifests() -> None:
    """将遗留 configs/*.json 归档到 .migrated/configs/，并删除 configs/ 目录。"""
    if not LEGACY_CONFIGS_DIR.is_dir():
        return
    MIGRATED_CONFIGS_ARCHIVE.mkdir(parents=True, exist_ok=True)
    legacy_devices = LEGACY_CONFIGS_DIR / "devices.json"
    if legacy_devices.exists() and not DEVICES_FILE.exists():
        MIGRATED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy_devices), str(DEVICES_FILE))
    elif legacy_devices.exists():
        legacy_devices.unlink(missing_ok=True)
    for cfg_path in LEGACY_CONFIGS_DIR.glob("*.json"):
        if cfg_path.name == "devices.json":
            continue
        cid = cfg_path.stem
        if not manifest_path_for(cid).exists():
            continue
        bak = MIGRATED_CONFIGS_ARCHIVE / f"{cid}.json.bak"
        if bak.exists():
            cfg_path.unlink(missing_ok=True)
        else:
            shutil.move(str(cfg_path), str(bak))
    _consolidate_legacy_configs_archive()
    remove_legacy_configs_dir()


def relocate_legacy_skill(mgr: Manager, name: str, repo_id: str) -> bool:
    """若技能仍在旧版扁平 Skills 目录，迁入当前配置的仓库子目录。"""
    legacy = LEGACY_SKILLS_DIR / name
    if not legacy.is_dir():
        return False
    dest = skill_dest(mgr, name, repo_id)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy), str(dest))
    return True


def config_skills_dir(mgr: Manager) -> Path:
    """当前配置下的 Skills 根目录。"""
    return config_dir(mgr.device_id) / "Skills"


def migrate_layout_v2() -> None:
    """将 configs/*.json + 扁平 Skills/ 迁移为按配置名分目录的布局。"""
    if LAYOUT_MIGRATION_FLAG.exists():
        return

    SM_ROOT.mkdir(parents=True, exist_ok=True)

    legacy_configs: list[Path] = []
    if LEGACY_CONFIGS_DIR.is_dir():
        legacy_configs = [
            p for p in LEGACY_CONFIGS_DIR.glob("*.json") if p.name != "devices.json"
        ]

    for cfg_path in legacy_configs:
        cid = cfg_path.stem
        target_manifest = manifest_path_for(cid)
        if not target_manifest.exists():
            target_manifest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cfg_path, target_manifest)
            (target_manifest.parent / "Skills").mkdir(exist_ok=True)

    primary_cid: str | None = None
    if ACTIVE_CONFIG_FILE.exists():
        primary_cid = ACTIVE_CONFIG_FILE.read_text(encoding="utf-8").strip() or None
    if not primary_cid and ACTIVE_DEVICE_FILE.exists():
        primary_cid = ACTIVE_DEVICE_FILE.read_text(encoding="utf-8").strip() or None
    if not primary_cid and legacy_configs:
        primary_cid = legacy_configs[0].stem

    if primary_cid and LEGACY_SKILLS_DIR.is_dir():
        manifest = manifest_path_for(primary_cid)
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            skills_root = config_dir(primary_cid) / "Skills"
            skills_root.mkdir(parents=True, exist_ok=True)
            migrated: set[str] = set()
            for repo in data.get("repos", []):
                repo_dir = skills_root / repo_slug(repo["id"])
                repo_dir.mkdir(parents=True, exist_ok=True)
                for sk in repo.get("skills", []):
                    if not sk.get("sync"):
                        continue
                    name = sk["name"]
                    old = LEGACY_SKILLS_DIR / name
                    if old.is_dir() and name not in migrated:
                        new = repo_dir / name
                        if not new.exists():
                            shutil.move(str(old), str(new))
                        migrated.add(name)
            local_dir = skills_root / "local"
            local_dir.mkdir(parents=True, exist_ok=True)
            for child in LEGACY_SKILLS_DIR.iterdir():
                if not child.is_dir() or child.name.startswith(".") or child.name in migrated:
                    continue
                dest = local_dir / child.name
                if not dest.exists():
                    shutil.move(str(child), str(dest))

    if ACTIVE_DEVICE_FILE.exists() and not ACTIVE_CONFIG_FILE.exists():
        ACTIVE_CONFIG_FILE.write_text(
            ACTIVE_DEVICE_FILE.read_text(encoding="utf-8"), encoding="utf-8",
        )

    LAYOUT_MIGRATION_FLAG.write_text("ok\n", encoding="utf-8")
    archive_legacy_manifests()


def ensure_workspace() -> None:
    """初始化 Skill Manager 工作区目录并部署启动器文件。"""
    SM_ROOT.mkdir(parents=True, exist_ok=True)
    AGENT_SKILLS.mkdir(parents=True, exist_ok=True)
    if LAYOUT_MIGRATION_FLAG.exists():
        archive_legacy_manifests()
    migrate_layout_v2()
    migrate_legacy_symlinks()
    load_settings()
    deploy_launcher_files()


def manager_script_path(mgr: Manager | None = None) -> Path:
    """解析 skill_manager.py 路径（优先 Local 安装副本）。"""
    if mgr is not None:
        local_script = skill_dest(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID) / "scripts" / "skill_manager.py"
        if local_script.is_file():
            return local_script
    did = resolve_device_id()
    local_script = config_skills_dir_for(did) / "local" / MANAGER_LINK_NAME / "scripts" / "skill_manager.py"
    if local_script.is_file():
        return local_script
    return SKILL_DIR / "scripts" / "skill_manager.py"


def config_skills_dir_for(config_id: str) -> Path:
    """返回某配置下的 Skills 根目录。"""
    return config_dir(config_id) / "Skills"


def watchdog_script_path(mgr: Manager | None = None) -> Path:
    """解析 watchdog.py 路径（优先 Local 安装副本）。"""
    if mgr is not None:
        local = skill_dest(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID) / "scripts" / "watchdog.py"
        if local.is_file():
            return local
    did = resolve_device_id()
    local = config_skills_dir_for(did) / "local" / MANAGER_LINK_NAME / "scripts" / "watchdog.py"
    if local.is_file():
        return local
    return WATCHDOG_SCRIPT


def watchdog_is_up(port: int | None = None) -> bool:
    """检测 watchdog 是否在线。"""
    import urllib.error
    import urllib.request

    p = port or WATCHDOG_PORT
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}/health", timeout=0.5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_watchdog_running(mgr: Manager | None = None) -> bool:
    """确保 watchdog 在后台运行（单例，带锁防并发重复拉起）。"""
    if watchdog_is_up():
        return True
    with _watchdog_lock:
        if watchdog_is_up():
            return True
        script = watchdog_script_path(mgr)
        if not script.is_file():
            return False
        subprocess.Popen(
            [sys.executable, str(script)],
            cwd=SM_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(20):
            if watchdog_is_up():
                return True
            time.sleep(0.1)
        return False


def deploy_gui_files() -> str:
    """
    将 sample GUI 部署到 Skill Manager 根目录（仅首次）。

    Returns:
        created | exists | missing_sample
    """
    if GUI_INDEX.is_file() and GUI_INDEX.stat().st_size > 0:
        return "exists"
    return sync_gui_index()


def _gui_index_ok() -> bool:
    """GUI 主文件存在且非空。"""
    return GUI_INDEX.is_file() and GUI_INDEX.stat().st_size > 0


def gui_index_config(mgr: Manager | None = None) -> dict:
    """生成注入 index.html 的本地服务配置。"""
    ensure_watchdog_running(mgr)
    port = int(os.environ.get("SM_PORT", str(DEFAULT_UI_PORT)))
    wd_port = int(os.environ.get("SM_WATCHDOG_PORT", str(WATCHDOG_PORT)))
    return {
        "serviceUrl": f"http://127.0.0.1:{port}",
        "watchdogUrl": f"http://127.0.0.1:{wd_port}",
    }


def render_gui_index(mgr: Manager | None = None) -> str:
    """从 sample 渲染 GUI，并注入本机启动配置。"""
    sample = SAMPLE_GUI_INDEX
    if not sample.is_file():
        legacy = SAMPLE_WEB_DIR / "index.html"
        sample = legacy if legacy.is_file() else sample
    if not sample.is_file():
        raise FileNotFoundError(f"缺少 GUI 模板: {SAMPLE_GUI_INDEX}")
    text = sample.read_text(encoding="utf-8")
    config = json.dumps(gui_index_config(mgr), ensure_ascii=False)
    if "const SM_CONFIG =" in text:
        return re.sub(
            r"const SM_CONFIG = \{[\s\S]*?\};",
            f"const SM_CONFIG = {config};",
            text,
            count=1,
        )
    return text.replace(
        "</head>",
        f"<script>const SM_CONFIG = {config};</script>\n</head>",
        1,
    )


def sync_gui_index(mgr: Manager | None = None) -> str:
    """同步 GUI 到工作区根目录并写入启动配置（原子写入）。"""
    SM_ROOT.mkdir(parents=True, exist_ok=True)
    content = render_gui_index(mgr)
    if not content.strip():
        raise RuntimeError("GUI 渲染结果为空，已中止写入")
    tmp = GUI_INDEX.with_suffix(".html.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(GUI_INDEX)
    return "synced"


def _portable_launcher_prelude() -> str:
    """生成 bash 前缀：以 .command 所在目录为 SM_ROOT，并定位 skill-manager 脚本。"""
    return """SM_ROOT="$(cd "$(dirname "$0")" && pwd)"
export SKILL_MANAGER_ROOT="$SM_ROOT"
cd "$SM_ROOT"
CFG=""
if [ -f "$SM_ROOT/.active-config" ]; then
  CFG="$(tr -d '[:space:]' < "$SM_ROOT/.active-config")"
elif [ -f "$SM_ROOT/.active-device" ]; then
  CFG="$(tr -d '[:space:]' < "$SM_ROOT/.active-device")"
fi
WD=""
if [ -n "$CFG" ] && [ -f "$SM_ROOT/$CFG/Skills/local/skill-manager/scripts/watchdog.py" ]; then
  WD="$SM_ROOT/$CFG/Skills/local/skill-manager/scripts/watchdog.py"
fi
if [ -z "$WD" ]; then
  WD="$(find "$SM_ROOT" -path '*/local/skill-manager/scripts/watchdog.py' -print -quit 2>/dev/null)"
fi
"""


def deploy_launcher_files(mgr: Manager | None = None) -> None:
    """将 Mac 快捷启动脚本部署到 Skill Manager 根目录（路径相对 .command 自身，可跨用户复制）。"""
    if sys.platform != "darwin":
        return
    SM_ROOT.mkdir(parents=True, exist_ok=True)
    wd_port = int(os.environ.get("SM_WATCHDOG_PORT", str(WATCHDOG_PORT)))
    port = int(os.environ.get("SM_PORT", str(DEFAULT_UI_PORT)))
    prelude = _portable_launcher_prelude()
    missing_msg = (
        "找不到 skill-manager。请确认已复制完整的 Skill Manager 文件夹，"
        "或从仓库运行 init。"
    )

    LAUNCHER_CMD.write_text(
        f"#!/bin/bash\n"
        f"set -e\n"
        f"{prelude}"
        f'if [ ! -f "$WD" ]; then\n'
        f'  osascript -e \'display alert "Skill Manager" message "{missing_msg}"\' 2>/dev/null || '
        f'echo "error: 找不到 watchdog.py" >&2\n'
        f"  exit 1\n"
        f"fi\n"
        f'if ! curl -sf "http://127.0.0.1:{wd_port}/health" >/dev/null 2>&1; then\n'
        f'  nohup python3 "$WD" >/dev/null 2>&1 &\n'
        f"  sleep 0.3\n"
        f"fi\n"
        f'curl -sf -X POST "http://127.0.0.1:{wd_port}/start" >/dev/null\n'
        f'open "http://127.0.0.1:{port}/"\n',
        encoding="utf-8",
    )
    LAUNCHER_CMD.chmod(0o755)

    obsolete_fix = SM_ROOT / "Fix Paths.command"
    if obsolete_fix.is_file():
        obsolete_fix.unlink()


def install_skill_manager_local(mgr: Manager, *, save: bool = True) -> bool:
    """将 skill-manager 复制到 Local 仓库并创建 Agent 软链。"""
    dest = skill_dest(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID)
    if not dest.exists():
        copy_skill_tree(SKILL_DIR, dest)
    else:
        wd_dest = dest / "scripts" / "watchdog.py"
        if not wd_dest.is_file() and WATCHDOG_SCRIPT.is_file():
            wd_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(WATCHDOG_SCRIPT, wd_dest)

    web_dir = dest / "web"
    for name in ("launcher.sample.html", "launcher.html"):
        (web_dir / name).unlink(missing_ok=True)

    local_repo = find_repo(mgr, LOCAL_REPO_ID)
    if not local_repo:
        return False

    skills_list = local_repo.setdefault("skills", [])
    entry = next((s for s in skills_list if s.get("name") == MANAGER_LINK_NAME), None)
    if entry is None:
        skills_list.append({
            "name": MANAGER_LINK_NAME,
            "source_path": f"local/{MANAGER_LINK_NAME}",
            "sync": True,
            "installed_at": now_iso(),
            "installed_commit": "local",
        })
    else:
        entry["sync"] = True
        entry["source_path"] = f"local/{MANAGER_LINK_NAME}"
        entry.setdefault("installed_at", now_iso())
        entry["installed_commit"] = "local"

    create_symlink(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID)
    if save:
        mgr.save()
    return True


def cleanup_obsolete_workspace_files(mgr: Manager | None = None) -> list[str]:
    """删除工作区中已废弃的 HTML 启动页与 launcher 模板。"""
    removed: list[str] = []
    for path in (LEGACY_LAUNCHER_HTML, OBSOLETE_LAUNCHER_CMD):
        if path.is_file():
            path.unlink()
            removed.append(path.name)

    if mgr is not None:
        web_dir = skill_dest(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID) / "web"
        for name in ("launcher.sample.html", "launcher.html"):
            obsolete = web_dir / name
            if obsolete.is_file():
                obsolete.unlink()
                try:
                    removed.append(str(obsolete.relative_to(SM_ROOT)))
                except ValueError:
                    removed.append(str(obsolete))
    return removed


def bootstrap_workspace(mgr: Manager) -> dict:
    """初始化后：部署 GUI 到工作区根目录，并将 skill-manager 装入 Local。"""
    with _bootstrap_lock:
        installed = True
        removed: list[str] = []
        if mgr.device_id not in _bootstrapped_devices:
            installed = install_skill_manager_local(mgr, save=False)
            mgr.save()
            removed = cleanup_obsolete_workspace_files(mgr)
            deploy_launcher_files(mgr)
            ensure_watchdog_running(mgr)
            _bootstrapped_devices.add(mgr.device_id)
        gui_status = sync_gui_index(mgr) if not _gui_index_ok() else "exists"
        return {"gui": gui_status, "skill_manager": installed, "removed_obsolete": removed}


def load_manager(device_id: str | None = None) -> Manager:
    """加载或初始化当前配置的管理器。"""
    ensure_workspace()
    did = resolve_device_id(device_id)
    path = manifest_path_for(did)
    legacy = legacy_manifest_path(did)

    if path.exists():
        raw = path.read_text(encoding="utf-8").strip()
        if raw:
            data = json.loads(raw)
        else:
            path.unlink(missing_ok=True)
            data = None
    else:
        data = None

    if data is None:
        if legacy.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy, path)
            data = json.loads(path.read_text(encoding="utf-8"))
            archive_legacy_manifests()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": MANIFEST_VERSION,
                "config_id": did,
                "device_id": did,
                "repos": [],
            }
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    (config_dir(did) / "Skills").mkdir(parents=True, exist_ok=True)
    mgr = Manager(device_id=did, manifest_path=path, data=data)
    ensure_builtin_repos(mgr)
    bootstrap_workspace(mgr)
    return mgr


def set_active_device(device_id: str) -> None:
    """持久化当前活跃配置（GUI 切换用）。"""
    ensure_workspace()
    ACTIVE_CONFIG_FILE.write_text(device_id + "\n", encoding="utf-8")
    ACTIVE_DEVICE_FILE.write_text(device_id + "\n", encoding="utf-8")


def sort_repos_for_display(repos: list[dict]) -> list[dict]:
    """仓库列表排序：Local 置顶。"""
    local = [r for r in repos if r.get("local") or r.get("id") == LOCAL_REPO_ID]
    rest = [r for r in repos if r not in local]
    return local + rest


def ensure_builtin_repos(mgr: Manager) -> None:
    """确保内置仓库存在（不可移除、别名固定）。"""
    changed = False
    repos = mgr.data.setdefault("repos", [])
    skills_root = config_skills_dir(mgr)
    skills_root.mkdir(parents=True, exist_ok=True)

    for spec in BUILTIN_REPOS:
        existing = find_repo(mgr, spec["id"])
        if existing:
            if not existing.get("builtin"):
                existing["builtin"] = True
                changed = True
            if existing.get("alias") != spec["alias"]:
                existing["alias"] = spec["alias"]
                changed = True
            if spec.get("local") and not existing.get("local"):
                existing["local"] = True
                changed = True
            continue

        if spec.get("local"):
            (skills_root / "local").mkdir(parents=True, exist_ok=True)
            repos.append({
                "id": spec["id"],
                "alias": spec["alias"],
                "builtin": True,
                "local": True,
                "skills": [],
            })
            changed = True
            continue

        cache = cache_dir_for(spec["id"])
        if not cache.exists():
            clone_repo(spec["url"], spec["branch"], cache)
        commit = git_head(cache)
        repos.insert(0, {
            "id": spec["id"],
            "url": spec["url"],
            "branch": spec["branch"],
            "alias": spec["alias"],
            "builtin": True,
            "cache_path": cache.relative_to(SM_ROOT).as_posix(),
            "last_commit": commit,
            "last_updated_at": git_commit_time(cache, commit) or now_iso(),
            "skills": [],
        })
        changed = True

    ordered = sort_repos_for_display(mgr.data["repos"])
    if [r.get("id") for r in ordered] != [r.get("id") for r in mgr.data["repos"]]:
        mgr.data["repos"] = ordered
        changed = True

    if changed:
        mgr.save()


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


def skill_dest(mgr: Manager, name: str, repo_id: str | None = None) -> Path:
    """本地技能安装目录（{配置}/Skills/{仓库}/{name}）。"""
    if repo_id is None:
        owner = find_skill_owner(mgr, name)
        repo_id = owner[0]["id"] if owner else LOCAL_REPO_ID
    return config_skills_dir(mgr) / repo_slug(repo_id) / name


def skill_link(mgr: Manager, name: str, agent_path: Path | None = None) -> Path:
    """Agent 技能目录下的软链接路径。"""
    base = agent_path if agent_path is not None else get_enabled_agent_paths()[0]
    return base / name


def find_synced_owner(mgr: Manager, skill_name: str) -> tuple[dict, dict] | None:
    """查找已同步（sync=true）该技能名的仓库与记录。"""
    for repo in mgr.data.get("repos", []):
        for sk in repo.get("skills", []):
            if sk.get("name") == skill_name and sk.get("sync"):
                return repo, sk
    return None


def synced_name_taken_by(mgr: Manager, skill_name: str, repo_id: str) -> str | None:
    """若其他仓库已同步同名技能，返回该仓库 id。"""
    owner = find_synced_owner(mgr, skill_name)
    if owner and owner[0].get("id") != repo_id:
        return owner[0]["id"]
    return None


def skill_link_ok(mgr: Manager, name: str, repo_id: str | None = None) -> bool:
    """检查技能软链是否指向指定仓库（或已同步归属仓库）的安装目录。"""
    if repo_id is None:
        owner = find_synced_owner(mgr, name)
        if not owner:
            return False
        repo_id = owner[0]["id"]
    dest = skill_dest(mgr, name, repo_id)
    if not dest.exists():
        return False
    dest_resolved = dest.resolve()
    for agent_path in get_enabled_agent_paths():
        link = agent_path / name
        if link.is_symlink() and link.resolve() == dest_resolved:
            return True
    return False


def find_skill_owner(mgr: Manager, skill_name: str) -> tuple[dict, dict] | None:
    """查找技能所属的仓库与记录。"""
    for repo in mgr.data.get("repos", []):
        for sk in repo.get("skills", []):
            if sk.get("name") == skill_name:
                return repo, sk
    return None


def check_name_conflict(mgr: Manager, skill_name: str, repo_id: str) -> str | None:
    """检查技能名是否已被其他仓库占用（已同步或 legacy 目录）。"""
    taken = synced_name_taken_by(mgr, skill_name, repo_id)
    if taken:
        return taken
    legacy = LEGACY_SKILLS_DIR / skill_name
    if legacy.is_dir():
        return "legacy"
    return None


def copy_skill_tree(src: Path, dest: Path) -> None:
    """覆盖复制技能目录到本地。"""

    def _ignore(_dir: str, names: list[str]) -> list[str]:
        return [n for n in names if n in {".git", "__pycache__", ".DS_Store"}]

    try:
        dest.resolve().relative_to(LEGACY_SKILLS_DIR.resolve())
        raise RuntimeError(f"拒绝写入旧版扁平目录: {dest}")
    except ValueError:
        pass
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=_ignore)


def create_symlink(mgr: Manager, name: str, repo_id: str | None = None) -> None:
    """在所有已启用 Agent 目录创建指向本地技能的软链。"""
    dest = skill_dest(mgr, name, repo_id)
    if not dest.exists():
        raise FileNotFoundError(f"技能目录不存在: {dest}")
    dest_resolved = dest.resolve()
    for agent_path in get_enabled_agent_paths():
        agent_path.mkdir(parents=True, exist_ok=True)
        link = agent_path / name
        if link.is_symlink() and link.resolve() == dest_resolved:
            continue
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(dest)


def remove_symlink(name: str) -> None:
    """从所有已启用 Agent 目录移除软链。"""
    for agent_path in get_enabled_agent_paths():
        link = agent_path / name
        if link.is_symlink() or link.is_file():
            link.unlink()
        elif link.is_dir() and not link.is_symlink():
            raise RuntimeError(f"{link} 是真实目录而非软链，请手动处理")


def discover_local_skills(mgr: Manager) -> list[DiscoveredSkill]:
    """扫描 Local 仓库目录下的技能。"""
    local_dir = config_skills_dir(mgr) / "local"
    results: list[DiscoveredSkill] = []
    if not local_dir.is_dir():
        return results
    for child in local_dir.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_md = child / "SKILL.md"
        if skill_md.is_file():
            name, desc = parse_frontmatter(skill_md)
        else:
            name, desc = child.name, ""
        results.append(
            DiscoveredSkill(
                name=name,
                source_path=f"local/{child.name}",
                description=desc,
                summary=summarize_description(desc),
            )
        )
    results.sort(key=lambda s: s.name)
    return results


def iter_synced_skills(mgr: Manager) -> list[tuple[dict, dict]]:
    """遍历配置中所有已同步技能 (repo, skill)。"""
    items: list[tuple[dict, dict]] = []
    for repo in mgr.data.get("repos", []):
        for sk in repo.get("skills", []):
            if sk.get("sync"):
                items.append((repo, sk))
    return items


def scan_disk_skills(mgr: Manager) -> dict[str, tuple[str, Path]]:
    """扫描磁盘上的技能目录，返回 name -> (repo_slug, path)。"""
    found: dict[str, tuple[str, Path]] = {}
    root = config_skills_dir(mgr)
    if not root.is_dir():
        return found
    for repo_dir in root.iterdir():
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        for skill_dir in repo_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                found[skill_dir.name] = (repo_dir.name, skill_dir)
    return found


def scan_agent_links() -> dict[str, Path]:
    """扫描已启用 Agent 目录中的软链，返回 name -> link path。"""
    links: dict[str, Path] = {}
    for agent_path in get_enabled_agent_paths():
        if not agent_path.is_dir():
            continue
        for entry in agent_path.iterdir():
            if entry.is_symlink():
                links[entry.name] = entry
    return links


def configured_repo_slugs(mgr: Manager) -> set[str]:
    """返回配置中所有仓库对应的 Skills 子目录名。"""
    return {repo_slug(r["id"]) for r in mgr.data.get("repos", [])}


def cleanup_orphan_empty_repo_dirs(mgr: Manager) -> list[str]:
    """
    删除 Skills 下不在配置中且无技能子目录的空仓库文件夹。

    ponytail: 仅删空目录；含 .DS_Store 等隐藏文件仍视为可删。
    """
    removed: list[str] = []
    root = config_skills_dir(mgr)
    if not root.is_dir():
        return removed
    configured = configured_repo_slugs(mgr)
    for repo_dir in list(root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        if repo_dir.name in configured:
            continue
        has_skill = any(
            c.is_dir() and not c.name.startswith(".")
            for c in repo_dir.iterdir()
        )
        if has_skill:
            continue
        shutil.rmtree(repo_dir)
        removed.append(repo_dir.name)
    return removed


def scan_local_disk_skills(mgr: Manager) -> dict[str, Path]:
    """扫描 local 目录下的技能文件夹（以磁盘为准）。"""
    found: dict[str, Path] = {}
    local_dir = config_skills_dir(mgr) / "local"
    if not local_dir.is_dir():
        return found
    for child in local_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            found[child.name] = child
    return found


def synced_skills_for_repo(repo: dict) -> dict[str, dict]:
    """返回仓库内 sync=true 的技能 name -> entry。"""
    return {
        s["name"]: s
        for s in repo.get("skills", [])
        if s.get("sync") and s.get("name")
    }


def is_local_repo(repo: dict) -> bool:
    """判断是否为 Local 内置仓库。"""
    return bool(repo.get("local") or repo.get("id") == LOCAL_REPO_ID)


def _remove_config_entry(mgr: Manager, name: str) -> bool:
    """将技能从配置中取消同步（sync=false）。"""
    owner = find_skill_owner(mgr, name)
    if not owner:
        return False
    owner[1]["sync"] = False
    return True


def _check_skill_links(
    mgr: Manager,
    name: str,
    repo_id: str,
    links: dict[str, Path],
    mismatches: list[dict],
) -> None:
    """检查已安装技能的 Agent 软链是否完整。"""
    dest = skill_dest(mgr, name, repo_id)
    if not dest.exists():
        return
    link = links.get(name)
    if link is None:
        mismatches.append(_enrich_mismatch({
            "id": f"missing_link:{name}",
            "type": "missing_link",
            "name": name,
            "repo_id": repo_id,
        }))
    elif not link.exists() or not link.resolve().exists():
        mismatches.append(_enrich_mismatch({
            "id": f"broken_link:{name}",
            "type": "broken_link",
            "name": name,
            "repo_id": repo_id,
        }))
    elif link.resolve() != dest.resolve():
        mismatches.append(_enrich_mismatch({
            "id": f"wrong_link:{name}",
            "type": "wrong_link",
            "name": name,
            "repo_id": repo_id,
        }))


def move_skill_to_local_repo(mgr: Manager, name: str, source: Path | None = None) -> bool:
    """
    将技能目录迁入 local 并登记到 Local 仓库（从其他仓库配置中移除）。

    Returns:
        是否完成迁移
    """
    local_repo = find_repo(mgr, LOCAL_REPO_ID)
    if not local_repo:
        return False

    local_dest = skill_dest(mgr, name, LOCAL_REPO_ID)
    local_dest.parent.mkdir(parents=True, exist_ok=True)

    if source is None:
        disk = scan_disk_skills(mgr)
        if name not in disk:
            return False
        source = disk[name][1]

    if source.resolve() != local_dest.resolve():
        if local_dest.exists():
            shutil.rmtree(local_dest)
        shutil.move(str(source), str(local_dest))

    for repo in mgr.data.get("repos", []):
        if repo.get("id") == LOCAL_REPO_ID:
            continue
        repo["skills"] = [s for s in repo.get("skills", []) if s.get("name") != name]

    skills_list = local_repo.setdefault("skills", [])
    entry = next((s for s in skills_list if s.get("name") == name), None)
    if entry is None:
        skills_list.append({
            "name": name,
            "source_path": f"local/{name}",
            "sync": True,
            "installed_at": now_iso(),
            "installed_commit": "local",
        })
    else:
        entry["sync"] = True
        entry["source_path"] = f"local/{name}"
        entry["installed_at"] = now_iso()
        entry["installed_commit"] = "local"

    if local_dest.exists():
        create_symlink(mgr, name, LOCAL_REPO_ID)
    return True


def _health_group(mtype: str, repo_slug: str = "") -> str:
    """健康检查分组：config_mismatch | extra_disk | extra_link。"""
    if mtype in ("stale_config", "missing_disk", "missing_link", "broken_link", "wrong_link"):
        return "config_mismatch"
    if mtype == "orphan_disk":
        return "extra_disk"
    return "extra_link"


def _health_hint(mtype: str, repo_slug: str = "") -> str:
    """健康检查项简短说明。"""
    if mtype == "orphan_disk" and repo_slug == "local":
        return "本地目录有技能，配置未记录"
    if mtype == "orphan_disk":
        return "磁盘有目录，配置未标记同步"
    return {
        "stale_config": "配置有记录，本地目录缺失",
        "missing_disk": "配置已同步，技能目录缺失",
        "missing_link": "未创建 Agents 软链",
        "broken_link": "软链已断裂",
        "wrong_link": "软链指向错误",
        "orphan_link": "软链存在，配置未记录",
    }.get(mtype, mtype)


def _health_actions(mtype: str, repo_slug: str = "") -> dict[str, bool]:
    """每项可用的修复操作。"""
    base = {"config_add": False, "config_remove": False, "skill_add": False, "skill_remove": False}
    if mtype == "stale_config":
        return {**base, "config_remove": True}
    if mtype in ("missing_disk", "missing_link", "broken_link", "wrong_link"):
        return {**base, "config_remove": True, "skill_add": True}
    if mtype == "orphan_disk" and repo_slug == "local":
        return {**base, "config_add": True}
    if mtype == "orphan_disk":
        return {**base, "skill_remove": True}
    if mtype == "orphan_link":
        return {**base, "config_add": True, "skill_remove": True}
    return base


def _enrich_mismatch(raw: dict) -> dict:
    """为不一致项补充分组、说明与可用操作。"""
    mtype = raw["type"]
    slug = raw.get("repo_slug", "")
    item = {
        **raw,
        "group": _health_group(mtype, slug),
        "hint": _health_hint(mtype, slug),
        "actions": _health_actions(mtype, slug),
    }
    if slug:
        item["detail"] = f"目录 {slug}/"
    elif raw.get("repo_id") and not is_local_repo({"id": raw["repo_id"]}):
        item["detail"] = f"配置仓库 {raw['repo_id']}"
    else:
        item["detail"] = ""
    return item


def _add_local_config_entry(mgr: Manager, name: str) -> None:
    """将技能登记到 Local 仓库配置。"""
    repo = find_repo(mgr, LOCAL_REPO_ID)
    if not repo:
        return
    skills_list = repo.setdefault("skills", [])
    entry = next((s for s in skills_list if s.get("name") == name), None)
    if entry is None:
        skills_list.append({
            "name": name,
            "source_path": f"local/{name}",
            "sync": True,
            "installed_at": now_iso(),
            "installed_commit": "local",
        })
    else:
        entry["sync"] = True
        entry["source_path"] = f"local/{name}"
        entry["installed_at"] = now_iso()
        entry["installed_commit"] = "local"


def healthcheck(mgr: Manager) -> dict:
    """
    对比配置、磁盘与软链。

    Local 仓库以 Skills/local/ 目录为准；GitHub 仓库以配置 sync 为准。

    Returns:
        ok, mismatches（供 GUI 修复）, removed_empty_dirs
    """
    removed_empty_dirs = cleanup_orphan_empty_repo_dirs(mgr)
    links = scan_agent_links()
    mismatches: list[dict] = []
    expected_synced: dict[str, str] = {}  # name -> repo_id

    local_repo = find_repo(mgr, LOCAL_REPO_ID)
    local_synced = synced_skills_for_repo(local_repo) if local_repo else {}
    local_disk = scan_local_disk_skills(mgr)

    for name in local_disk:
        if name not in local_synced:
            mismatches.append(_enrich_mismatch({
                "id": f"orphan_disk:local:{name}",
                "type": "orphan_disk",
                "name": name,
                "repo_slug": "local",
                "repo_id": LOCAL_REPO_ID,
            }))
        else:
            expected_synced[name] = LOCAL_REPO_ID
            _check_skill_links(mgr, name, LOCAL_REPO_ID, links, mismatches)

    for name in local_synced:
        if name not in local_disk:
            mismatches.append(_enrich_mismatch({
                "id": f"stale_config:{name}",
                "type": "stale_config",
                "name": name,
                "repo_id": LOCAL_REPO_ID,
                "repo_slug": "local",
            }))
        else:
            expected_synced[name] = LOCAL_REPO_ID

    for repo in mgr.data.get("repos", []):
        if is_local_repo(repo):
            continue
        repo_id = repo["id"]
        slug = repo_slug(repo_id)
        synced = synced_skills_for_repo(repo)
        repo_disk_dir = config_skills_dir(mgr) / slug

        for name in synced:
            expected_synced[name] = repo_id
            dest = skill_dest(mgr, name, repo_id)
            if not dest.exists():
                mismatches.append(_enrich_mismatch({
                    "id": f"missing_disk:{name}",
                    "type": "missing_disk",
                    "name": name,
                    "repo_id": repo_id,
                    "repo_slug": slug,
                }))
            else:
                _check_skill_links(mgr, name, repo_id, links, mismatches)

        if not repo_disk_dir.is_dir():
            continue
        for child in repo_disk_dir.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.name not in synced:
                mismatches.append(_enrich_mismatch({
                    "id": f"orphan_disk:{slug}:{child.name}",
                    "type": "orphan_disk",
                    "name": child.name,
                    "repo_slug": slug,
                    "repo_id": repo_id,
                }))

    for name, link in links.items():
        if name in expected_synced:
            continue
        if link.exists() and link.resolve().exists():
            mismatches.append(_enrich_mismatch({
                "id": f"orphan_link:{name}",
                "type": "orphan_link",
                "name": name,
            }))
        else:
            link.unlink(missing_ok=True)

    return {
        "ok": not mismatches,
        "mismatches": mismatches,
        "removed_empty_dirs": removed_empty_dirs,
    }


def apply_healthcheck_action(
    mgr: Manager,
    item: dict,
    action: str,
    *,
    save: bool = True,
) -> bool:
    """
    对单项不一致执行指定修复操作。

    action: config_add | config_remove | skill_add | skill_remove
    """
    valid = {"config_add", "config_remove", "skill_add", "skill_remove"}
    if action not in valid:
        raise ValueError(f"未知操作: {action}")

    mtype = item.get("type", "")
    name = item.get("name", "")
    slug = item.get("repo_slug", "")
    if not name:
        return False

    if action == "config_remove":
        if mtype in ("stale_config", "missing_disk", "missing_link", "broken_link", "wrong_link"):
            if not _remove_config_entry(mgr, name):
                return False
        else:
            return False
    elif action == "config_add":
        if mtype == "orphan_disk" and slug == "local":
            _add_local_config_entry(mgr, name)
            create_symlink(mgr, name, LOCAL_REPO_ID)
        elif mtype == "orphan_link":
            _add_local_config_entry(mgr, name)
            if skill_dest(mgr, name, LOCAL_REPO_ID).exists():
                create_symlink(mgr, name, LOCAL_REPO_ID)
        else:
            return False
    elif action == "skill_add":
        if mtype == "missing_disk":
            owner = find_skill_owner(mgr, name)
            if not owner or is_local_repo(owner[0]):
                return False
            install_skill(mgr, owner[0]["id"], name, save=False)
        elif mtype in ("missing_link", "broken_link", "wrong_link"):
            owner = find_skill_owner(mgr, name)
            if not owner or not skill_dest(mgr, name, owner[0]["id"]).exists():
                return False
            create_symlink(mgr, name, owner[0]["id"])
        else:
            return False
    elif action == "skill_remove":
        if mtype == "orphan_disk" and slug != "local":
            disk = scan_disk_skills(mgr)
            if name in disk and disk[name][1].exists():
                shutil.rmtree(disk[name][1])
        elif mtype == "orphan_link":
            remove_symlink(name)
        else:
            return False

    if save:
        mgr.save()
    return True


def apply_healthcheck_actions(mgr: Manager, actions: list[dict]) -> dict:
    """批量执行健康检查修复操作。"""
    fixed: list[str] = []
    for act in actions:
        item = act.get("item") or act
        action = act.get("action", "")
        if apply_healthcheck_action(mgr, item, action, save=False):
            fixed.append(f"{item.get('name')}:{action}")
    mgr.save()
    return {"fixed": fixed}


def apply_healthcheck_fix(mgr: Manager, mode: str, items: list[dict]) -> dict:
    """
    按用户选择修复健康检查不一致项。

    mode: config（改配置）| skills（改技能文件/软链）
    """
    if mode not in ("config", "skills"):
        raise ValueError("mode 须为 config 或 skills")

    fixed: list[str] = []
    for item in items:
        mtype = item.get("type", "")
        name = item.get("name", "")
        slug = item.get("repo_slug", "")
        if not name:
            continue

        if mode == "config":
            if mtype in ("stale_config", "missing_disk", "missing_link", "broken_link", "wrong_link"):
                if _remove_config_entry(mgr, name):
                    fixed.append(name)
            elif mtype == "orphan_disk" and slug == "local":
                _add_local_config_entry(mgr, name)
                create_symlink(mgr, name, LOCAL_REPO_ID)
                fixed.append(name)
            elif mtype == "orphan_link":
                _add_local_config_entry(mgr, name)
                fixed.append(name)
        else:
            if mtype == "missing_disk":
                owner = find_skill_owner(mgr, name)
                if owner and not is_local_repo(owner[0]):
                    install_skill(mgr, owner[0]["id"], name, save=False)
                    fixed.append(name)
            elif mtype in ("missing_link", "broken_link", "wrong_link"):
                owner = find_skill_owner(mgr, name)
                if owner and skill_dest(mgr, name, owner[0]["id"]).exists():
                    create_symlink(mgr, name, owner[0]["id"])
                    fixed.append(name)
            elif mtype == "orphan_disk" and slug != "local":
                disk = scan_disk_skills(mgr)
                if name in disk and disk[name][1].exists():
                    shutil.rmtree(disk[name][1])
                fixed.append(name)
            elif mtype == "orphan_link":
                remove_symlink(name)
                fixed.append(name)

    mgr.save()
    return {"fixed": fixed, "mode": mode}


def relink_config_skills(mgr: Manager) -> list[str]:
    """为当前配置中所有已同步技能重建软链。"""
    linked: list[str] = []
    for repo, sk in iter_synced_skills(mgr):
        name = sk["name"]
        if skill_dest(mgr, name, repo["id"]).exists():
            create_symlink(mgr, name, repo["id"])
            linked.append(name)
    return linked


def clear_config_symlinks(mgr: Manager) -> list[str]:
    """移除当前配置所有已同步技能的 Agent 软链。"""
    cleared: list[str] = []
    for _repo, sk in iter_synced_skills(mgr):
        remove_symlink(sk["name"])
        cleared.append(sk["name"])
    return cleared


def switch_config(old_id: str, new_id: str, *, relink: bool = False) -> dict:
    """切换活跃配置，可选同步切换软链。"""
    if new_id not in list_device_configs():
        raise ValueError(f"配置不存在: {new_id}")
    if relink and old_id != new_id:
        old_mgr = load_manager(old_id)
        clear_config_symlinks(old_mgr)
    set_active_device(new_id)
    result: dict = {"config_id": new_id}
    if relink:
        new_mgr = load_manager(new_id)
        result["linked"] = relink_config_skills(new_mgr)
    return result


def config_create(display_name: str) -> dict:
    """创建新配置目录与 manifest。"""
    name = display_name.strip()
    if not name:
        raise ValueError("配置名称不能为空")
    cid = sanitize_device_id(name)
    if not cid:
        raise ValueError("配置名称无效")
    if config_dir(cid).exists() or legacy_manifest_path(cid).exists():
        raise ValueError(f"配置已存在: {cid}")

    config_dir(cid).mkdir(parents=True)
    (config_dir(cid) / "Skills").mkdir()
    data = {
        "version": MANIFEST_VERSION,
        "config_id": cid,
        "display_name": name,
        "device_id": cid,
        "repos": [],
    }
    path = manifest_path_for(cid)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mgr = Manager(device_id=cid, manifest_path=path, data=data)
    ensure_builtin_repos(mgr)
    return {"config_id": cid, "display_name": name}


def config_delete(config_id: str) -> dict:
    """删除配置及其技能库目录。"""
    cid = config_id.strip()
    if not cid:
        raise ValueError("config_id 不能为空")
    configs = list_device_configs()
    if cid not in configs:
        raise ValueError(f"配置不存在: {cid}")
    if len(configs) <= 1:
        raise ValueError("至少保留一个配置")
    if cid == resolve_device_id():
        raise ValueError("不能删除当前活跃配置，请先切换到其他配置")

    target = config_dir(cid)
    if target.exists():
        shutil.rmtree(target)
    legacy = legacy_manifest_path(cid)
    if legacy.exists():
        legacy.unlink()

    return {"deleted": cid}


def config_copy(source_id: str, new_name: str) -> dict:
    """复制配置目录及技能库为新配置。"""
    name = new_name.strip()
    if not name:
        raise ValueError("配置名称不能为空")
    src_id = source_id.strip()
    new_cid = sanitize_device_id(name)
    if not new_cid:
        raise ValueError("配置名称无效")
    if new_cid == src_id:
        raise ValueError("新名称与源配置相同")
    if config_dir(new_cid).exists() or legacy_manifest_path(new_cid).exists():
        raise ValueError(f"配置已存在: {new_cid}")

    src = config_dir(src_id)
    if not src.exists():
        raise ValueError(f"源配置不存在: {src_id}")

    shutil.copytree(src, config_dir(new_cid))
    path = manifest_path_for(new_cid)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["config_id"] = new_cid
    data["device_id"] = new_cid
    data["display_name"] = name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return read_config_meta(new_cid)


def config_rename(config_id: str, new_name: str) -> dict:
    """重命名配置（含目录名与 display_name）。"""
    name = new_name.strip()
    if not name:
        raise ValueError("配置名称不能为空")
    old_cid = config_id.strip()
    new_cid = sanitize_device_id(name)
    if not new_cid:
        raise ValueError("配置名称无效")

    src = config_dir(old_cid)
    if not src.exists():
        raise ValueError(f"配置不存在: {old_cid}")

    if new_cid != old_cid:
        if config_dir(new_cid).exists() or legacy_manifest_path(new_cid).exists():
            raise ValueError(f"配置已存在: {new_cid}")
        shutil.move(str(src), str(config_dir(new_cid)))
        if resolve_device_id() == old_cid:
            set_active_device(new_cid)

    path = manifest_path_for(new_cid)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["config_id"] = new_cid
    data["device_id"] = new_cid
    data["display_name"] = name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return read_config_meta(new_cid)


def read_config_meta(config_id: str) -> dict:
    """读取配置元信息。"""
    path = manifest_path_for(config_id)
    if not path.exists():
        legacy = legacy_manifest_path(config_id)
        if legacy.exists():
            path = legacy
        else:
            return {
                "config_id": config_id,
                "display_name": config_id,
                "repo_count": 0,
                "skill_count": 0,
            }
    data = json.loads(path.read_text(encoding="utf-8"))
    repos = data.get("repos", [])
    repo_count = len(repos)
    skill_count = sum(
        1 for repo in repos for sk in repo.get("skills", []) if sk.get("sync")
    )
    return {
        "config_id": config_id,
        "display_name": data.get("display_name") or config_id,
        "repo_count": repo_count,
        "skill_count": skill_count,
        "path": str(config_dir(config_id)),
    }


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
    if repo.get("builtin"):
        raise ValueError("内置仓库不可移除")

    uninstalled: list[str] = []
    if purge:
        for sk in list(repo.get("skills", [])):
            if sk.get("sync"):
                uninstall_skill(mgr, sk["name"], save=False)
                uninstalled.append(sk["name"])

    mgr.data["repos"] = [r for r in mgr.data["repos"] if r.get("id") != repo_id]
    mgr.save()
    return {"removed": repo_id, "uninstalled": uninstalled}


def repo_update_alias(mgr: Manager, repo_id: str, alias: str) -> dict:
    """设置或清除仓库显示别名。"""
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")
    if repo.get("builtin"):
        raise ValueError("内置仓库别名不可修改")
    alias = alias.strip()
    if alias:
        repo["alias"] = alias
    else:
        repo.pop("alias", None)
    mgr.save()
    return repo


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

    if repo.get("local"):
        discovered = discover_local_skills(mgr)
        repo_time = repo_updated_at(repo)
    else:
        cache = repo_cache_path(repo)
        if not cache.exists():
            clone_repo(repo["url"], repo.get("branch", "main"), cache)
        discovered = discover_skills_in_repo(cache)
        repo_time = repo_updated_at(repo)

    synced = {sk["name"]: sk for sk in repo.get("skills", [])}
    result = []
    seen: set[str] = set()
    for sk in discovered:
        seen.add(sk.name)
        existing = synced.get(sk.name)
        sync_here = bool(existing and existing.get("sync"))
        taken_by = synced_name_taken_by(mgr, sk.name, repo_id)
        installed_at = None
        if sync_here:
            installed_at = existing.get("installed_at")
        result.append({
            "name": sk.name,
            "source_path": sk.source_path,
            "description": sk.description,
            "summary": sk.summary,
            "sync": sync_here,
            "installed_commit": existing.get("installed_commit") if existing else None,
            "installed_at": installed_at,
            "repo_updated_at": repo_time,
            "link_ok": skill_link_ok(mgr, sk.name, repo_id) if sync_here else False,
            "name_taken_by": taken_by or "",
        })
    for name, existing in synced.items():
        if name in seen:
            continue
        sync_here = bool(existing.get("sync"))
        taken_by = synced_name_taken_by(mgr, name, repo_id)
        result.append({
            "name": name,
            "source_path": existing.get("source_path", ""),
            "description": "",
            "summary": "",
            "sync": sync_here,
            "installed_commit": existing.get("installed_commit"),
            "installed_at": existing.get("installed_at"),
            "repo_updated_at": repo_time,
            "link_ok": skill_link_ok(mgr, name, repo_id) if sync_here else False,
            "name_taken_by": taken_by or "",
        })
    result.sort(key=lambda x: x["name"])
    return result


def install_skill(
    mgr: Manager,
    repo_id: str,
    skill_ref: str,
    *,
    save: bool = True,
) -> dict:
    """
    安装技能：复制到配置 Skills 目录（按仓库分子目录）并创建软链。

    skill_ref 可以是技能 name 或 source_path。
    """
    repo = find_repo(mgr, repo_id)
    if not repo:
        raise ValueError(f"仓库不存在: {repo_id}")

    if repo.get("local"):
        discovered = {sk.name: sk for sk in discover_local_skills(mgr)}
        by_path = {sk.source_path: sk for sk in discovered.values()}
        sk = discovered.get(skill_ref) or by_path.get(skill_ref)
        if not sk:
            raise ValueError(f"未找到本地技能: {skill_ref}")
        conflict = check_name_conflict(mgr, sk.name, repo_id)
        if conflict:
            raise ValueError(f"技能名 '{sk.name}' 已被仓库 {conflict} 占用")
        dest = skill_dest(mgr, sk.name, LOCAL_REPO_ID)
        if not dest.exists():
            raise ValueError(f"本地技能目录不存在: {dest}")
        create_symlink(mgr, sk.name, LOCAL_REPO_ID)
        commit = "local"
    else:
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

        dest_dir = config_skills_dir(mgr) / repo_slug(repo_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = skill_dest(mgr, sk.name, repo_id)
        if not relocate_legacy_skill(mgr, sk.name, repo_id):
            src = cache / sk.source_path
            copy_skill_tree(src, dest)
        create_symlink(mgr, sk.name, repo_id)
        commit = git_head(cache)
        repo["last_commit"] = commit
        touch_repo_updated(repo)

    skills_list = repo.setdefault("skills", [])
    entry = next((s for s in skills_list if s.get("name") == sk.name), None)
    if entry is None:
        entry = {"name": sk.name, "source_path": sk.source_path}
        skills_list.append(entry)
    entry["source_path"] = sk.source_path
    entry["installed_commit"] = commit
    entry["installed_at"] = now_iso()
    entry["sync"] = True

    if save:
        mgr.save()
    return {"name": sk.name, "source_path": sk.source_path, "commit": commit}


def uninstall_skill(
    mgr: Manager,
    skill_name: str,
    *,
    repo_id: str | None = None,
    save: bool = True,
) -> dict:
    """卸载技能：删除本地副本、软链和 manifest 记录。"""
    if repo_id:
        repo = find_repo(mgr, repo_id)
        if not repo:
            raise ValueError(f"仓库不存在: {repo_id}")
        if not any(s.get("name") == skill_name for s in repo.get("skills", [])):
            raise ValueError(f"技能不在仓库 {repo_id}: {skill_name}")
        rid = repo_id
    else:
        owner = find_skill_owner(mgr, skill_name)
        rid = owner[0]["id"] if owner else LOCAL_REPO_ID
    dest = skill_dest(mgr, skill_name, rid)
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
        if repo.get("local"):
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

            rid = repo["id"]
            dest_dir = config_skills_dir(mgr) / repo_slug(rid)
            dest_dir.mkdir(parents=True, exist_ok=True)
            copy_skill_tree(src, skill_dest(mgr, sk["name"], rid))
            create_symlink(mgr, sk["name"], rid)
            sk["installed_commit"] = remote_commit
            sk["installed_at"] = now_iso()
            updated.append({
                "name": sk["name"],
                "repo": repo["id"],
                "commit": remote_commit,
            })

    mgr.save()
    return updated


def is_skill_path_excluded(rel_path: str) -> bool:
    """判断 SKILL.md 路径是否在排除目录中。"""
    parts = Path(rel_path).parts
    dir_parts = parts[:-1] if parts and parts[-1] == "SKILL.md" else parts
    return any(p in EXCLUDE_PARTS or p.startswith(".") for p in dir_parts)


def git_ensure_commits(cache: Path, *commits: str) -> None:
    """确保浅克隆缓存中存在指定 commit（按需 fetch）。"""
    for commit in commits:
        if not commit or commit in ("local", ""):
            continue
        try:
            run_git(["rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=cache)
        except RuntimeError:
            run_git(["fetch", "origin", commit, "--depth", "1"], cwd=cache)


def skill_dirs_at_commit(cache: Path, commit: str) -> set[str]:
    """返回某 commit 下所有技能目录（含 SKILL.md 的父路径）。"""
    if not commit or commit in ("local", ""):
        return set()
    git_ensure_commits(cache, commit)
    try:
        out = run_git(["ls-tree", "-r", "--name-only", commit], cwd=cache)
    except RuntimeError:
        return set()
    dirs: set[str] = set()
    for line in out.splitlines():
        line = line.strip()
        if not line.endswith("SKILL.md") or is_skill_path_excluded(line):
            continue
        dirs.add(Path(line).parent.as_posix())
    return dirs


def git_diff_name_status(
    cache: Path,
    old_commit: str,
    new_commit: str,
    path: str = "",
) -> list[tuple[str, str]]:
    """返回 git diff --name-status 的 (状态, 文件路径) 列表。"""
    if not old_commit or old_commit in ("local", "") or old_commit == new_commit:
        return []
    git_ensure_commits(cache, old_commit, new_commit)
    try:
        args = ["diff", "--name-status", old_commit, new_commit]
        if path:
            args += ["--", path]
        out = run_git(args, cwd=cache)
    except RuntimeError:
        return []
    results: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            results.append((status, parts[2]))
        elif len(parts) >= 2:
            results.append((status, parts[-1]))
    return results


def summarize_file_changes(changes: list[tuple[str, str]], source_path: str) -> str | None:
    """
    汇总技能目录内的文件增删改。

    Returns:
        如「新增 2、删除 1、修改 3 个文件」；无变化时返回 None。
    """
    prefix = source_path.rstrip("/") + "/"
    added = deleted = modified = 0
    samples: list[str] = []
    for status, fp in changes:
        if not (fp.startswith(prefix) or fp == source_path):
            continue
        base = fp[len(prefix):] if fp.startswith(prefix) else fp
        if status.startswith("A"):
            added += 1
        elif status.startswith("D"):
            deleted += 1
        else:
            modified += 1
        if len(samples) < 3:
            samples.append(Path(base).name)
    total = added + deleted + modified
    if total == 0:
        return None
    parts: list[str] = []
    if added:
        parts.append(f"新增 {added}")
    if deleted:
        parts.append(f"删除 {deleted}")
    if modified:
        parts.append(f"修改 {modified}")
    detail = f"（{', '.join(samples)}{'…' if total > len(samples) else ''}）"
    return "、".join(parts) + f" 个文件{detail}"


def skill_info_at_path(cache: Path, source_path: str) -> DiscoveredSkill | None:
    """从缓存工作区读取指定路径的技能信息。"""
    skill_md = cache / source_path / "SKILL.md"
    if not skill_md.is_file():
        return None
    name, description = parse_frontmatter(skill_md)
    return DiscoveredSkill(
        name=name,
        source_path=source_path,
        description=description,
        summary=summarize_description(description),
    )


def repo_baseline_commit(repo: dict) -> str:
    """取仓库用于对比的基准 commit。"""
    baseline = repo.get("last_commit") or ""
    if baseline:
        return baseline
    synced = [
        s.get("installed_commit", "")
        for s in repo.get("skills", [])
        if s.get("sync") and s.get("installed_commit")
    ]
    return synced[0] if synced else ""


def collect_repo_updates(
    repo: dict,
    cache: Path,
    remote_commit: str,
    remote_time: str,
) -> list[dict]:
    """收集单个仓库的可展示更新项（仅新增/删除/文件变更）。"""
    updates: list[dict] = []
    baseline = repo_baseline_commit(repo)
    synced_by_path = {
        s.get("source_path", ""): s
        for s in repo.get("skills", [])
        if s.get("sync")
    }

    if baseline and baseline != remote_commit:
        old_dirs = skill_dirs_at_commit(cache, baseline)
        new_dirs = skill_dirs_at_commit(cache, remote_commit)
        for sp in sorted(new_dirs - old_dirs):
            info = skill_info_at_path(cache, sp)
            if not info:
                continue
            updates.append({
                "repo_id": repo["id"],
                "name": info.name,
                "source_path": sp,
                "change_type": "new",
                "summary": "云端新增技能",
                "local_commit": baseline[:8],
                "remote_commit": remote_commit[:8],
                "local_updated_at": repo.get("last_updated_at"),
                "remote_updated_at": remote_time,
            })
        for sp in sorted(old_dirs - new_dirs):
            sk = synced_by_path.get(sp)
            if not sk:
                continue
            updates.append({
                "repo_id": repo["id"],
                "name": sk["name"],
                "source_path": sp,
                "change_type": "deleted",
                "summary": "云端已删除此技能",
                "local_commit": (sk.get("installed_commit") or baseline)[:8],
                "remote_commit": remote_commit[:8],
                "local_updated_at": sk.get("installed_at"),
                "remote_updated_at": remote_time,
            })

    deleted_paths = {
        u["source_path"] for u in updates if u.get("change_type") == "deleted"
    }
    new_paths = {
        u["source_path"] for u in updates if u.get("change_type") == "new"
    }

    for sk in repo.get("skills", []):
        if not sk.get("sync"):
            continue
        sp = sk.get("source_path", "")
        if sp in deleted_paths or sp in new_paths:
            continue
        local_commit = sk.get("installed_commit") or baseline
        if local_commit == remote_commit:
            continue
        if not (cache / sp).exists():
            continue
        changes = git_diff_name_status(cache, local_commit, remote_commit, sp)
        summary = summarize_file_changes(changes, sp)
        if not summary:
            continue
        updates.append({
            "repo_id": repo["id"],
            "name": sk["name"],
            "source_path": sp,
            "change_type": "modified",
            "summary": summary,
            "local_commit": local_commit[:8] if local_commit else "—",
            "remote_commit": remote_commit[:8],
            "local_updated_at": sk.get("installed_at"),
            "remote_updated_at": remote_time,
        })

    return updates


def check_updates(mgr: Manager) -> dict:
    """
    检查云端仓库与本地差异（仅 fetch，不覆盖本地）。

    仅返回三类变更：新增技能、删除技能、技能目录内文件增删改。

    Returns:
        {"checked_at": "...", "updates": [...]}
    """
    updates: list[dict] = []

    for repo in mgr.data.get("repos", []):
        if repo.get("local"):
            continue

        cache = repo_cache_path(repo)
        if not cache.exists():
            clone_repo(repo["url"], repo.get("branch", "main"), cache)

        branch = repo.get("branch", "main")
        try:
            remote_commit = git_fetch(cache, branch)
        except RuntimeError:
            remote_commit = git_head(cache)

        remote_time = git_commit_time(cache, remote_commit)
        updates.extend(collect_repo_updates(repo, cache, remote_commit, remote_time))

    return {"checked_at": now_iso(), "updates": updates}


def apply_updates(mgr: Manager, items: list[dict]) -> list[dict]:
    """应用用户选中的变更：新增→安装、删除→卸载、修改→覆盖更新。"""
    updated: list[dict] = []
    for item in items:
        repo_id = item.get("repo_id", "")
        name = item.get("name", "")
        if not repo_id or not name:
            continue
        change_type = item.get("change_type", "modified")
        if change_type == "new":
            ref = item.get("source_path") or name
            r = install_skill(mgr, repo_id, ref, save=False)
            updated.append({**r, "repo": repo_id, "change_type": "new"})
        elif change_type == "deleted":
            uninstall_skill(mgr, name, save=False)
            updated.append({"name": name, "repo": repo_id, "change_type": "deleted"})
        else:
            for r in update_skills(mgr, repo_id, name):
                updated.append({**r, "change_type": "modified"})
    mgr.save()
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
        if sync:
            if name not in discovered:
                continue
            install_skill(mgr, repo_id, name, save=False)
            installed.append(name)
        else:
            repo = find_repo(mgr, repo_id)
            if not repo:
                continue
            if not any(s.get("name") == name and s.get("sync") for s in repo.get("skills", [])):
                continue
            uninstall_skill(mgr, name, repo_id=repo_id, save=False)
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
    """汇总当前配置状态。"""
    hc = healthcheck(mgr)
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
    """返回当前配置及可用配置列表。"""
    configs = list_device_configs()
    current = mgr.device_id
    if current not in configs:
        configs = sorted(set(configs + [current]))
    meta = read_config_meta(current)
    return {
        "current": {
            "config_id": current,
            "device_id": current,
            "display_name": meta["display_name"],
            "hostname": socket.gethostname(),
            "manifest_path": str(mgr.manifest_path),
            "skills_path": str(config_skills_dir(mgr)),
        },
        "available": [read_config_meta(c) for c in configs],
    }


# --- CLI -------------------------------------------------------------------

def cmd_healthcheck(args: argparse.Namespace) -> int:
    """执行健康检查并打印结果。"""
    mgr = load_manager(args.device)
    report = healthcheck(mgr)
    if report.get("ok"):
        print("配置、技能目录与软链一致。")
        return 0
    for item in report.get("mismatches", []):
        hint = item.get("hint", item.get("type", ""))
        name = item.get("name", "")
        detail = item.get("detail", "")
        line = f"{name}: {hint}"
        if detail:
            line += f" ({detail})"
        print(line)
    return 1


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
    print(f"发现 {len(updates)} 项变更（{result.get('checked_at')}）:")
    type_labels = {"new": "新增", "deleted": "删除", "modified": "变更"}
    for u in updates:
        label = type_labels.get(u.get("change_type", ""), "?")
        print(f"  [{label}] [{u['repo_id']}] {u['name']}: {u.get('summary', '')}")
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
    mgr = load_manager(_args.device)
    print(f"工作区: {SM_ROOT}")
    print(f"技能目录: {config_skills_dir(mgr)}")
    print(f"配置文件: {mgr.manifest_path}")
    print(f"GUI: {GUI_INDEX} ({'已部署' if GUI_INDEX.is_file() else '缺失'})")
    print(f"Local 技能: {skill_dest(mgr, MANAGER_LINK_NAME, LOCAL_REPO_ID)}")
    print(f"管理脚本: {manager_script_path(mgr)}")
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
