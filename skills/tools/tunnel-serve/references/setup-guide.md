# Setup Guide (one-time)

首次使用前须有 **`config.env`**，再运行 bootstrap。详见 `config-variables.md`。

```bash
# 1. 配置（若尚无 config.env）
bash scripts/init-config.sh

# 2. 初始化 Cloudflare Tunnel（每台机器一次）
bash scripts/bootstrap.sh
```

## What bootstrap does

### 0. Reads `config.env`

使用 `TS_ZONE`、`TS_SUBDOMAIN`、`TS_TUNNEL_NAME`、`TS_PORT` 生成公网主机名
`https://${TS_SUBDOMAIN}.${TS_ZONE}/` 与本地 ingress。

### 1. Installs `cloudflared` (if missing)

Via Homebrew: `brew install cloudflared`. Linux 见
[Cloudflare 文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

### 2. Logs you in

```bash
cloudflared tunnel login
```

Opens a browser. **Select the zone matching `TS_ZONE`** and authorize.
Creates `~/.cloudflared/cert.pem`. Skipped if already present.

### 3. Creates the tunnel

```bash
cloudflared tunnel create <TS_TUNNEL_NAME>
```

Writes credentials to `~/.cloudflared/<UUID>.json`.

### 4. Writes `~/.cloudflared/config.yml`

```yaml
tunnel: <tunnel-uuid>
credentials-file: /Users/<you>/.cloudflared/<uuid>.json

ingress:
  - hostname: <TS_SUBDOMAIN>.<TS_ZONE>
    service: http://127.0.0.1:<TS_PORT>
  - service: http_status:404
```

### 5. Creates the DNS route

```bash
cloudflared tunnel route dns <TS_TUNNEL_NAME> <TS_DOMAIN>
```

CNAME `<TS_DOMAIN> → <tunnel-uuid>.cfargotunnel.com` (proxied). Idempotent.

## Verify

```bash
bash scripts/status.sh
```

Smoke test (replace domain with your `TS_DOMAIN`):

```bash
bash scripts/expose.sh SKILL.md smoke
curl -I http://127.0.0.1:8787/smoke/
# wait ~5s, then:
curl -I "https://${TS_SUBDOMAIN}.${TS_ZONE}/smoke/"
bash scripts/close.sh smoke
```

## Files created

| File | Purpose |
|------|---------|
| `config.env` | 本机域名/隧道配置（用户维护，不入库） |
| `~/.cloudflared/cert.pem` | login 产生的 origin cert |
| `~/.cloudflared/<uuid>.json` | 隧道凭证（保密） |
| `~/.cloudflared/config.yml` | 本地 ingress |
| `state/*` | 运行时 PID、路由表、日志 |

## Uninstall / redo

```bash
cloudflared tunnel delete <TS_TUNNEL_NAME>
rm ~/.cloudflared/config.yml
```

Edit `config.env` if needed, then re-run `bootstrap.sh`.
