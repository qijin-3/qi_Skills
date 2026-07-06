# Setup Guide (one-time)

This walks through `scripts/bootstrap.sh` and explains each step. Run it once;
after that all daily use is local and instant.

```bash
bash scripts/bootstrap.sh
```

## What bootstrap does

### 1. Installs `cloudflared` (if missing)
Via Homebrew: `brew install cloudflared`. Verify it exists:
```bash
brew info cloudflared
```
cloudflared is the Cloudflare Tunnel client. It runs **on your Mac** (not in
Docker), keeping an outbound connection to Cloudflare's edge.

### 2. Logs you in
```bash
cloudflared tunnel login
```
Opens a browser. **Select the `jinqi33.top` zone** and click Authorize. This
drops `~/.cloudflared/cert.pem` (an origin cert that lets cloudflared create
tunnels and DNS routes for your account). Safe to re-run; skipped if
`cert.pem` exists.

> If the browser doesn't open, the terminal prints a URL — copy it into a
> browser manually.

### 3. Creates the `share` tunnel
```bash
cloudflared tunnel create share
```
Creates a named tunnel and writes its credentials to
`~/.cloudflared/<UUID>.json`. bootstrap records this as `~/.cloudflared/share.json`-style.
The tunnel has a UUID; bootstrap resolves it via `cloudflared tunnel list`.

> This tunnel is **completely separate** from the Docker `cloudflared-tunnel`
> container that serves miniflux. They share only the Cloudflare account.

### 4. Writes `~/.cloudflared/config.yml`
```yaml
tunnel: <tunnel-uuid>
credentials-file: /Users/<you>/.cloudflared/<uuid>.json

ingress:
  - hostname: share.jinqi33.top
    service: http://127.0.0.1:8787
  - service: http_status:404
```
This is the **local** ingress config (vs. the dashboard-managed remote config
your Docker tunnel uses). `share.jinqi33.top` → the local router server on
8787; anything else → 404.

### 5. Creates the DNS route
```bash
cloudflared tunnel route dns share share.jinqi33.top
```
Creates a CNAME `share.jinqi33.top → <tunnel-uuid>.cfargotunnel.com` (proxied).
Idempotent — if the record exists it just says so.

## Verify it worked

After bootstrap completes:

```bash
bash scripts/status.sh
# config: line should point to ~/.cloudflared/config.yml
```

Then expose a smoke test and check both locally and publicly:
```bash
bash scripts/expose.sh SKILL.md smoke
curl -I http://127.0.0.1:8787/smoke/        # local: expect 200
# wait ~5s for the tunnel to register, then:
curl -I https://share.jinqi33.top/smoke/     # public: expect 200
bash scripts/close.sh smoke                   # clean up
```

If the public URL fails but local works, see `troubleshooting.md`.

## Files created (all under ~/.cloudflared and this skill's state/)

| File | Purpose |
|------|---------|
| `~/.cloudflared/cert.pem` | origin cert from `login` |
| `~/.cloudflared/<uuid>.json` | tunnel credentials (keep secret) |
| `~/.cloudflared/config.yml` | local ingress config |
| `state/*` | runtime: PIDs, registry, deadline, logs |

## Uninstall / redo

To remove the tunnel entirely:
```bash
cloudflared tunnel delete share     # deletes tunnel + (optionally) DNS
rm ~/.cloudflared/config.yml
```
Re-run `bootstrap.sh` to recreate.
