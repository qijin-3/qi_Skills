---
name: tunnel-serve
description: >-
  Expose local HTML files or folders to the public internet through a dedicated
  local Cloudflare Tunnel at the fixed subdomain share.jinqi33.top. Use when the
  user wants to: "把本地 HTML 暴露到公网", "通过 share.jinqi33.top 访问本地文件",
  "临时分享这个网页/页面", "把本地页面分享出去", "tunnel serve", "暴露本地 html",
  "share this html", "公开本地网页", "给这个页面一个网址/URL", or otherwise needs a
  public URL for local static content. Supports both single files and whole
  folders of related HTML (e.g. daily reports). Runs a local cloudflared tunnel
  named "share", fully isolated from the user's existing Docker miniflux tunnel.
---

# tunnel-serve

Expose local HTML files or folders at a public URL via a **local** Cloudflare
Tunnel (named `share`), completely separate from the user's existing Docker
`cloudflared-tunnel` container that serves miniflux.

**Fixed subdomain `share.jinqi33.top`**, different content reached by URL
**path**. The tunnel and router server start together on demand and stop
together (manual or auto after 1h).

- Scenario A — single HTML file: `expose doc/report.html` → `https://share.jinqi33.top/report/`
- Scenario B — folder of related HTML: `expose out/` → directory listing at `https://share.jinqi33.top/out/`

## Architecture

```
Mac host:
  serve.py   (router, 127.0.0.1:8787)  ←  cloudflared (tunnel "share")
                                              │ direct localhost, no host.docker.internal
                                              ▼
                                    Cloudflare edge → https://share.jinqi33.top

Separate & untouched: the Docker `cloudflared-tunnel` container (miniflux).
```

## First-time setup (ONCE)

Run the bootstrap script. It installs `cloudflared` (via brew) if missing,
walks you through `cloudflared tunnel login` (opens a browser — you pick the
`jinqi33.top` zone), creates a tunnel named `share`, writes the local
`config.yml`, and creates the DNS route. After this you never touch
Cloudflare again.

```bash
bash scripts/bootstrap.sh
```

See **`references/setup-guide.md`** for details and what each step does.

## Daily commands

All commands live in `scripts/`. Run from this skill's directory.

### Expose a file or folder
```bash
bash scripts/expose.sh <path-to-file-or-folder> [custom-slug]
```
- Starts `serve.py` **and** `cloudflared` together if not already running.
- `custom-slug` optional; defaults to a slug derived from the file/folder name.
- Returns the public URL.

```bash
# Scenario A: single file
bash scripts/expose.sh doc/report.html
# → https://share.jinqi33.top/report/

# Scenario B: a folder of daily reports (auto-lists all HTML inside)
bash scripts/expose.sh ~/reports/2026-07 daily-tech
# → https://share.jinqi33.top/daily-tech/
```

### Close
```bash
bash scripts/close.sh [slug]   # remove one route (tunnel+server keep running if other routes remain)
bash scripts/close.sh          # stop BOTH cloudflared + serve.py, clear all routes
```

### Status
```bash
bash scripts/status.sh
# prints: serve.py + cloudflared running? auto-shutdown countdown? all routes?
```

### Adjust auto-shutdown time
```bash
bash scripts/extend.sh 120     # 120 minutes from now
bash scripts/extend.sh 0       # never auto-shut (until manual close)
```

## How it works

```
you: expose foo.html
  → expose.sh starts serve.py (8787) AND cloudflared (tunnel "share") if not up
  → adds {slug: foo, path: /abs/foo.html} to state/registry.json
  → returns https://share.jinqi33.top/foo/

browser → https://share.jinqi33.top/foo/
  → Cloudflare edge → local cloudflared → 127.0.0.1:8787
  → serve.py reads registry.json → returns file (or folder listing)
```

`serve.py` binds to **127.0.0.1 only** — only the local cloudflared can reach
it; nothing is exposed on the LAN.

## Operational notes

- **Two processes, one lifecycle**: `serve.py` and `cloudflared` start together
  (first `expose`) and stop together (last `close` or auto-shutdown). Both PIDs
  are tracked in `state/`.
- **Auto-shutdown** defaults to 1 hour so nothing stays open accidentally.
  `extend.sh 0` keeps it up indefinitely.
- **Isolation**: this tunnel is named `share` and runs locally. It does NOT
  touch the Docker `cloudflared-tunnel` container or the miniflux route.
- **Paths in the registry are absolute**, so cwd doesn't matter.

## References

- `references/setup-guide.md` — bootstrap walkthrough and what it does
- `references/troubleshooting.md` — login issues, tunnel won't connect, port conflicts
