#!/usr/bin/env python3
"""tunnel-serve router server.

Serves files/folders registered in state/registry.json over HTTP on
127.0.0.1:8787. Each registry entry maps a URL slug to an absolute local path.
  GET /                 -> index of all active routes
  GET /<slug>/          -> directory listing (folder) or file contents (file)
  GET /<slug>/<sub>     -> file inside a registered folder

Self-shuts down when state/deadline.txt timestamp passes. A deadline value of
the literal "NEVER" disables auto-shutdown.

Pure standard library (http.server, json, html, mimetypes, os, time).
"""

import html
import json
import mimetypes
import os
import re
import signal
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# --- Paths -----------------------------------------------------------------
SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = SKILL_DIR / "state"
REGISTRY = STATE_DIR / "registry.json"
DEADLINE = STATE_DIR / "deadline.txt"
LOG = STATE_DIR / "server.log"

HOST = "127.0.0.1"
PORT = 8787
SLUG_RE = re.compile(r"^[a-z0-9-]{1,63}$")
CHECK_INTERVAL = 5.0  # seconds between deadline checks


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_registry() -> dict:
    try:
        return json.loads(REGISTRY.read_text())
    except Exception:
        return {}


def deadline_expired() -> bool:
    try:
        raw = DEADLINE.read_text().strip()
    except Exception:
        return False
    if raw == "NEVER" or not raw:
        return False
    try:
        return time.time() > int(raw)
    except ValueError:
        return False


def shutdown_if_expired(watcher_check) -> None:
    """Background watchdog: exit the process when deadline passes."""
    while True:
        time.sleep(CHECK_INTERVAL)
        if deadline_expired():
            log("deadline reached, shutting down")
            os.kill(os.getpid(), signal.SIGTERM)
            return


def guess_content_type(path: str) -> str:
    ctype, _ = mimetypes.guess_type(path)
    # Python 3.14 may not register some types by default
    if ctype is None:
        ext = Path(path).suffix.lower()
        if ext in (".html", ".htm"):
            ctype = "text/html; charset=utf-8"
        elif ext == ".css":
            ctype = "text/css; charset=utf-8"
        elif ext == ".js":
            ctype = "application/javascript; charset=utf-8"
        elif ext == ".json":
            ctype = "application/json; charset=utf-8"
        elif ext == ".svg":
            ctype = "image/svg+xml"
        else:
            ctype = "application/octet-stream"
    return ctype


def safe_join(base: Path, untrusted: str) -> Path | None:
    """Join base dir with a subpath, refusing to escape the base."""
    target = (base / untrusted).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    return target


class Handler(BaseHTTPRequestHandler):
    server_version = "tunnel-serve/1.0"

    # ---- helpers ----------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_text(self, code: int, msg: str) -> None:
        self._send(code, msg.encode("utf-8"), "text/plain; charset=utf-8")

    def _redirect(self, location: str) -> None:
        self.send_response(301)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---- routing ----------------------------------------------------------
    def do_GET(self):
        self.route()

    def do_HEAD(self):
        self.route()

    def route(self):
        # Normalize: strip query, keep path
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        # urllib unquote for percent-encoded names inside folders
        from urllib.parse import unquote
        path = unquote(path)

        if path == "/" or path == "":
            return self.serve_index()

        # Split into slug and remainder
        parts = path.strip("/").split("/", 1)
        slug = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""

        if not SLUG_RE.match(slug):
            return self._send_text(404, f"Invalid slug: {slug}")

        reg = load_registry()
        entry = reg.get(slug)
        if not entry:
            return self._send_text(404, f"No route registered for: {slug}")

        local_path = Path(entry["path"]) if isinstance(entry, dict) else Path(entry)
        if not local_path.exists():
            return self._send_text(404, f"Registered path no longer exists: {local_path}")

        if local_path.is_file():
            # File target: ignore remainder; serve the file directly.
            if remainder:
                return self._send_text(404, "This route serves a single file.")
            return self.serve_file(local_path)

        # Directory target
        if remainder:
            sub = safe_join(local_path, remainder)
            if sub is None:
                return self._send_text(400, "Invalid path.")
            if sub.is_file():
                return self.serve_file(sub)
            if sub.is_dir():
                # ensure trailing slash so relative links work
                if not path.endswith("/"):
                    return self._redirect(f"/{slug}/{remainder}/")
                return self.serve_dir(sub, slug, remainder)
            return self._send_text(404, "Not found.")
        else:
            # root of the directory route; ensure trailing slash
            if not path.endswith("/"):
                return self._redirect(f"/{slug}/")
            return self.serve_dir(local_path, slug, "")

    # ---- responses --------------------------------------------------------
    def serve_index(self) -> None:
        reg = load_registry()
        rows = []
        for slug, entry in sorted(reg.items()):
            path = entry["path"] if isinstance(entry, dict) else entry
            kind = "📁 folder" if Path(path).is_dir() else "📄 file"
            rows.append(
                f'<li><a href="/{slug}/">{html.escape(slug)}</a> '
                f'<span class="meta">{kind} · {html.escape(path)}</span></li>'
            )
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>tunnel-serve</title>"
            "<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;"
            "max-width:780px;margin:40px auto;padding:0 16px;color:#222}"
            "h1{font-size:20px}ul{list-style:none;padding:0}"
            "li{padding:6px 0;border-bottom:1px solid #eee}"
            "a{color:#0a66c2;text-decoration:none}a:hover{text-decoration:underline}"
            ".meta{color:#888;font-size:13px;margin-left:8px}"
            ".empty{color:#888}</style></head><body>"
            f"<h1>tunnel-serve · {len(reg)} active route(s)</h1>"
        )
        if rows:
            body += "<ul>" + "".join(rows) + "</ul>"
        else:
            body += "<p class='empty'>No routes registered yet.</p>"
        body += "</body></html>"
        self._send(200, body.encode("utf-8"))

    def serve_dir(self, dirpath: Path, slug: str, rel: str) -> None:
        try:
            entries = sorted(dirpath.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return self._send_text(403, "Permission denied.")

        prefix = f"/{slug}/{rel}".rstrip("/") + "/"
        rows = []
        if rel:  # not top of route -> allow going up
            rows.append(f'<li><a href="{prefix}..">../</a></li>')
        for e in entries:
            name = e.name
            disp = html.escape(name + ("/" if e.is_dir() else ""))
            rows.append(f'<li><a href="{prefix}{html.escape(name)}{"/" if e.is_dir() else ""}">{disp}</a></li>')

        title = f"/{slug}/{rel}".rstrip("/")
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title>"
            "<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;"
            "max-width:780px;margin:40px auto;padding:0 16px;color:#222}"
            "h1{font-size:18px;font-weight:500}ul{list-style:none;padding:0}"
            "li{padding:5px 0}a{color:#0a66c2;text-decoration:none}a:hover{text-decoration:underline}"
            "</style></head><body>"
            f"<h1>Index of <code>{html.escape(title)}</code></h1><ul>"
            + "".join(rows)
            + "</ul></body></html>"
        )
        self._send(200, body.encode("utf-8"))

    def serve_file(self, filepath: Path) -> None:
        try:
            data = filepath.read_bytes()
        except PermissionError:
            return self._send_text(403, "Permission denied.")
        except FileNotFoundError:
            return self._send_text(404, "File not found.")
        ctype = guess_content_type(str(filepath))
        self._send(200, data, ctype)

    def log_message(self, fmt, *args):  # quieter; real logging via log()
        return


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        REGISTRY.write_text("{}")

    # Watchdog thread
    import threading
    t = threading.Thread(target=shutdown_if_expired, args=(CHECK_INTERVAL,), daemon=True)
    t.start()

    # Graceful shutdown on SIGTERM/SIGINT
    def handle_signal(signum, frame):
        log(f"received signal {signum}, stopping")
        sys.exit(0)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.server_close()
        log("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
