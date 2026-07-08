#!/usr/bin/env python3
"""
轻量守护进程：允许浏览器通过 HTTP 启动主 GUI 服务（无需执行 .command）。

默认监听 127.0.0.1:8790，主服务端口 8791。
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_manager as sm  # noqa: E402

HOST = "127.0.0.1"
PORT = int(os.environ.get("SM_WATCHDOG_PORT", "8790"))
MAIN_PORT = int(os.environ.get("SM_PORT", str(sm.DEFAULT_UI_PORT)))


def port_in_use(port: int) -> bool:
    """检测端口是否已被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


def main_server_up() -> bool:
    """检测主 GUI 服务是否在线。"""
    try:
        with urllib.request.urlopen(
            f"http://{HOST}:{MAIN_PORT}/api/status", timeout=0.5,
        ) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_main_server() -> None:
    """后台启动主 GUI 服务（已有实例则跳过）。"""
    if port_in_use(MAIN_PORT):
        return
    script = sm.manager_script_path()
    env = os.environ.copy()
    env["SKILL_MANAGER_ROOT"] = str(sm.SM_ROOT)
    subprocess.Popen(
        [sys.executable, str(script), "ui", "--no-open", "--port", str(MAIN_PORT)],
        cwd=sm.SM_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def wait_main_server(timeout_s: float = 10.0) -> bool:
    """等待主服务就绪。"""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if main_server_up():
            return True
        time.sleep(0.25)
    return False


class Handler(BaseHTTPRequestHandler):
    """Watchdog HTTP 处理器。"""

    def log_message(self, _fmt, *_args) -> None:
        return

    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/health", "/"):
            self._send_json(200, {"ok": True, "main": main_server_up()})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/start":
            self.send_response(404)
            self.end_headers()
            return
        if not main_server_up():
            start_main_server()
            ready = wait_main_server()
        else:
            ready = True
        self._send_json(200 if ready else 503, {"ok": ready, "main": ready})


def run_watchdog(port: int = PORT) -> None:
    """启动 watchdog HTTP 服务（阻塞）；端口已占用则直接退出。"""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((HOST, port))
    except OSError:
        return
    finally:
        probe.close()
    server = ThreadingHTTPServer((HOST, port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run_watchdog()
