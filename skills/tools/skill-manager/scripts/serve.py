#!/usr/bin/env python3
"""
技能管理器 Web 服务：提供 REST API 和 GUI 静态页面。

纯标准库实现，默认监听 127.0.0.1:8791。
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import signal
import subprocess
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

# 同目录模块
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_manager as sm  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = SKILL_DIR / "web"
HOST = "127.0.0.1"
DEFAULT_PORT = 8791

# 进程级设备覆盖（GUI 切换后生效）
_active_device: str | None = None


def log(msg: str) -> None:
    """向终端输出带时间戳的日志。"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def log_error(method: str, path: str, msg: str) -> None:
    """向终端 stderr 输出 API 错误。"""
    line = f"[{time.strftime('%H:%M:%S')}] ERROR {method} {path} → {msg}"
    print(line, file=sys.stderr, flush=True)


def get_mgr() -> sm.Manager:
    """加载当前活跃设备的管理器。"""
    return sm.load_manager(_active_device)


def json_response(handler: BaseHTTPRequestHandler, code: int, data: dict) -> None:
    """发送 JSON 响应。"""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler: BaseHTTPRequestHandler) -> dict:
    """读取并解析请求体 JSON。"""
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def guess_content_type(path: Path) -> str:
    """推断文件 MIME 类型。"""
    ctype, _ = mimetypes.guess_type(str(path))
    if ctype:
        return ctype
    ext = path.suffix.lower()
    if ext in (".html", ".htm"):
        return "text/html; charset=utf-8"
    if ext == ".css":
        return "text/css; charset=utf-8"
    if ext == ".js":
        return "application/javascript; charset=utf-8"
    return "application/octet-stream"


class Handler(BaseHTTPRequestHandler):
    """HTTP 请求处理器。"""

    server_version = "skill-manager/1.0"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def do_PUT(self):
        self._route()

    def do_DELETE(self):
        self._route()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _route(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/" or path == "/index.html":
            return self._serve_file(WEB_DIR / "index.html")

        if path.startswith("/web/"):
            rel = path[len("/web/"):]
            target = (WEB_DIR / rel).resolve()
            try:
                target.relative_to(WEB_DIR.resolve())
            except ValueError:
                return json_response(self, 403, {"error": "forbidden"})
            if target.is_file():
                return self._serve_file(target)
            return json_response(self, 404, {"error": "not found"})

        if not path.startswith("/api/"):
            log_error(self.command, path, "not found")
            return json_response(self, 404, {"error": "not found"})

        try:
            return self._api(path, self.command)
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            log_error(self.command, path, str(exc))
            return json_response(self, 400, {"error": str(exc)})
        except json.JSONDecodeError as exc:
            log_error(self.command, path, f"无效 JSON: {exc}")
            return json_response(self, 400, {"error": "无效 JSON 请求体"})
        except Exception as exc:
            log_error(self.command, path, str(exc))
            traceback.print_exc()
            return json_response(self, 500, {"error": str(exc)})

    def _serve_file(self, filepath: Path) -> None:
        """提供静态文件。"""
        if not filepath.exists():
            return json_response(self, 404, {"error": "not found"})
        data = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", guess_content_type(filepath))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _api(self, path: str, method: str) -> None:
        """路由 REST API。"""
        global _active_device
        mgr = get_mgr()

        if path == "/api/device" and method == "GET":
            return json_response(self, 200, sm.get_device_info(mgr))

        if path == "/api/device/switch" and method == "POST":
            body = read_body(self)
            device_id = (body.get("config_id") or body.get("device_id") or "").strip()
            if not device_id:
                raise ValueError("config_id 不能为空")
            relink = bool(body.get("relink", False))
            old_id = mgr.device_id
            result = sm.switch_config(old_id, device_id, relink=relink)
            _active_device = device_id
            mgr = get_mgr()
            info = sm.get_device_info(mgr)
            return json_response(self, 200, {**info, **result})

        if path == "/api/configs" and method == "GET":
            return json_response(self, 200, {
                "configs": [sm.read_config_meta(c) for c in sm.list_device_configs()],
                "current": mgr.device_id,
            })

        if path == "/api/configs" and method == "POST":
            body = read_body(self)
            created = sm.config_create(body.get("name", ""))
            return json_response(self, 201, created)

        m = re.match(r"^/api/configs/(.+)/copy$", path)
        if m and method == "POST":
            config_id = m.group(1)
            body = read_body(self)
            result = sm.config_copy(config_id, body.get("name", ""))
            return json_response(self, 201, result)

        m = re.match(r"^/api/configs/(.+)$", path)
        if m:
            config_id = m.group(1)
            if method == "PUT":
                body = read_body(self)
                result = sm.config_rename(config_id, body.get("name", ""))
                _active_device = result["config_id"]
                return json_response(self, 200, result)
            if method == "DELETE":
                result = sm.config_delete(config_id)
                return json_response(self, 200, result)

        if path == "/api/repos" and method == "GET":
            repos = []
            for repo in mgr.data.get("repos", []):
                synced = sum(1 for s in repo.get("skills", []) if s.get("sync"))
                if repo.get("local"):
                    skill_count = len(sm.discover_local_skills(mgr))
                else:
                    cache = sm.repo_cache_path(repo)
                    skill_count = (
                        len(sm.discover_skills_in_repo(cache))
                        if cache.exists()
                        else 0
                    )
                repos.append({
                    "id": repo["id"],
                    "alias": repo.get("alias", ""),
                    "builtin": bool(repo.get("builtin")),
                    "local": bool(repo.get("local")),
                    "url": repo.get("url"),
                    "branch": repo.get("branch", "main"),
                    "last_commit": repo.get("last_commit", ""),
                    "last_updated_at": sm.repo_updated_at(repo),
                    "synced_count": synced,
                    "skill_count": skill_count,
                })
            repos = sm.sort_repos_for_display(repos)
            return json_response(self, 200, {"repos": repos})

        if path == "/api/repos" and method == "POST":
            body = read_body(self)
            repo = sm.repo_add(mgr, body["url"], body.get("branch", "main"))
            return json_response(self, 201, {"repo": repo})

        m = re.match(r"^/api/repos/(.+)/skills$", path)
        if m:
            repo_id = m.group(1)
            if method == "GET":
                skills = sm.discover_repo(mgr, repo_id)
                return json_response(self, 200, {"skills": skills})
            if method == "PUT":
                body = read_body(self)
                result = sm.sync_skills_batch(mgr, repo_id, body.get("skills", []))
                return json_response(self, 200, result)

        m = re.match(r"^/api/repos/(.+)$", path)
        if m:
            repo_id = m.group(1)
            if method == "PUT":
                body = read_body(self)
                if "branch" in body:
                    repo = sm.repo_update_branch(mgr, repo_id, body["branch"])
                    return json_response(self, 200, {"repo": repo})
                if "alias" in body:
                    repo = sm.repo_update_alias(mgr, repo_id, body.get("alias", ""))
                    return json_response(self, 200, {"repo": repo})
                raise ValueError("无有效更新字段")
            if method == "DELETE":
                purge = read_body(self).get("purge", False)
                result = sm.repo_remove(mgr, repo_id, purge=purge)
                return json_response(self, 200, result)

        m = re.match(r"^/api/skills/(.+)$", path)
        if m and method == "DELETE":
            name = m.group(1)
            result = sm.uninstall_skill(mgr, name)
            return json_response(self, 200, result)

        if path == "/api/update" and method == "POST":
            body = read_body(self)
            updated = sm.update_skills(mgr, body.get("repo_id"), body.get("skill"))
            return json_response(self, 200, {"updated": updated})

        if path == "/api/updates/check" and method == "POST":
            result = sm.check_updates(mgr)
            return json_response(self, 200, result)

        if path == "/api/updates/apply" and method == "POST":
            body = read_body(self)
            updated = sm.apply_updates(mgr, body.get("items", []))
            return json_response(self, 200, {"updated": updated})

        if path == "/api/skills/batch" and method == "POST":
            body = read_body(self)
            result = sm.sync_skills_multi(mgr, body.get("actions", []))
            return json_response(self, 200, result)

        if path == "/api/status" and method == "GET":
            return json_response(self, 200, sm.get_status(mgr))

        if path == "/api/healthcheck" and method == "POST":
            report = sm.healthcheck(mgr)
            return json_response(self, 200, report)

        if path == "/api/healthcheck/apply" and method == "POST":
            body = read_body(self)
            result = sm.apply_healthcheck_fix(
                mgr, body.get("mode", ""), body.get("items", []),
            )
            return json_response(self, 200, result)

        if path == "/api/settings" and method == "GET":
            return json_response(self, 200, sm.get_settings_info())

        if path == "/api/settings" and method == "PUT":
            body = read_body(self)
            result = sm.update_settings(body.get("agents", []))
            return json_response(self, 200, result)

        if path == "/api/settings/open" and method == "POST":
            body = read_body(self)
            opened = sm.open_agent_path(body.get("path", ""))
            return json_response(self, 200, {"opened": opened})

        log_error(method, path, "API not found")
        json_response(self, 404, {"error": "not found"})


def run_server(port: int = DEFAULT_PORT, device_id: str | None = None, open_browser: bool = True) -> None:
    """启动 Web 服务。"""
    global _active_device
    _active_device = device_id

    if open_browser:
        url = f"http://{HOST}:{port}/"
        subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def handle_signal(signum, _frame):
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    server = ThreadingHTTPServer((HOST, port), Handler)
    log(f"技能管理器 GUI: http://{HOST}:{port}/")
    log("API 错误将打印到此终端（stderr）")
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("SM_PORT", str(DEFAULT_PORT)))
    run_server(port=port, open_browser="--no-open" not in sys.argv)
