# Troubleshooting

Diagnose from the inside out: local server → cloudflared → Cloudflare edge → DNS.

## Quick check
```bash
bash scripts/status.sh
```
Confirms both processes are up and the config exists.

## The public URL doesn't load

### 1. Is the router up locally?
```bash
curl -I http://127.0.0.1:8787/
# expect HTTP 200
```
If not, the router isn't running. `expose` starts it; if it failed, check:
```bash
cat state/server.log
```
Common cause: port 8787 in use by something else.
```bash
lsof -nP -iTCP:8787 -sTCP:LISTEN
```

### 2. Is cloudflared running and connected?
```bash
bash scripts/status.sh          # shows cloudflared pid
tail -20 state/cloudflared.log
```
A healthy log shows lines like `Registered tunnel connection`. If you see
repeated connection failures (e.g. on a restrictive network), cloudflared
will keep retrying — it recovers automatically once the network allows.

If cloudflared isn't running at all, restart via:
```bash
bash scripts/close.sh && bash scripts/expose.sh <some-file>
```

### 3. Did bootstrap actually complete?
```bash
ls ~/.cloudflared/              # cert.pem, <uuid>.json, config.yml should exist
cat ~/.cloudflared/config.yml   # tunnel + ingress for share.jinqi33.top
```
If `config.yml` or the credentials json is missing, re-run:
```bash
bash scripts/bootstrap.sh
```

### 4. Does the DNS CNAME exist?
```bash
cloudflared tunnel route dns share share.jinqi33.top
# idempotent: if missing it creates it; if present it says so
```
Or check in the Cloudflare dashboard → `jinqi33.top` → DNS: there should be a
proxied CNAME `share → <tunnel-uuid>.cfargotunnel.com`.

### 5. Wrong content / stale
Routes are keyed by slug; re-exposing with the same slug updates instantly.
The server sends `Cache-Control: no-store`, but a hard reload (Cmd+Shift+R)
rules out browser cache.

## cloudflared login didn't open a browser
`cloudflared tunnel login` prints a URL in the terminal. Copy it into a
browser manually. After authorizing, make sure you selected `jinqi33.top`.

## "tunnel not set up yet" error
You're running an expose/close before bootstrap. Run:
```bash
bash scripts/bootstrap.sh
```

## Port 8787 already in use
```bash
lsof -nP -iTCP:8787 -sTCP:LISTEN
```
Either stop the other process, or change the port: edit `TS_PORT` in
`scripts/lib.sh`, `PORT` in `scripts/serve.py`, and the `service:` URL in
`~/.cloudflared/config.yml` to match.

## A route points to a missing file
`status.sh` shows `⚠️ missing`. The file moved or was deleted. Re-expose with
the new path, or `close.sh <slug>` to remove it.

## Relationship to the Docker miniflux tunnel
None. This skill runs a **separate, local** tunnel named `share`. It does not
read or modify the Docker `cloudflared-tunnel` container or its config. If
miniflux stops working, it's unrelated to this skill.

## Reset everything
```bash
bash scripts/close.sh           # stop processes, clear routes
rm -f state/*.log               # optional: clear logs
```
To fully remove the tunnel:
```bash
cloudflared tunnel delete share
rm ~/.cloudflared/config.yml
```
