# Troubleshooting

从里到外排查：本地 router → cloudflared → Cloudflare 边缘 → DNS。

## Quick check

```bash
bash scripts/status.sh
```

若提示 config 问题，见 `config-variables.md`。

## config.env missing or incomplete

```bash
bash scripts/init-config.sh
# 或
cp config.env.example config.env   # 编辑 TS_ZONE / TS_SUBDOMAIN / TS_TUNNEL_NAME
```

## Public URL doesn't load

### 1. Local router up?

```bash
# 端口以 config.env 中 TS_PORT 为准，默认 8787
curl -I http://127.0.0.1:8787/
```

若失败，查看 `state/server.log`。常见原因：端口被占用。

```bash
lsof -nP -iTCP:8787 -sTCP:LISTEN
```

### 2. cloudflared running?

```bash
bash scripts/status.sh
tail -20 state/cloudflared.log
```

健康日志含 `Registered tunnel connection`。重启：

```bash
bash scripts/close.sh && bash scripts/expose.sh <some-file>
```

### 3. Bootstrap complete?

```bash
ls ~/.cloudflared/
cat ~/.cloudflared/config.yml   # hostname 应为 config.env 中的 TS_DOMAIN
```

缺少文件则：

```bash
bash scripts/bootstrap.sh
```

### 4. DNS CNAME exists?

```bash
source config.env 2>/dev/null || true
cloudflared tunnel route dns "$TS_TUNNEL_NAME" "${TS_SUBDOMAIN}.${TS_ZONE}"
```

或在 Cloudflare Dashboard → `TS_ZONE` → DNS：应有 proxied CNAME
`<TS_SUBDOMAIN> → <tunnel-uuid>.cfargotunnel.com`。

### 5. Wrong zone at login

`cert.pem` 须对应 `TS_ZONE`。若 login 时选错 Zone，删除 cert 后重登：

```bash
rm ~/.cloudflared/cert.pem
bash scripts/bootstrap.sh
```

## Login didn't open browser

`cloudflared tunnel login` 会打印 URL，手动打开浏览器，并选择 **`TS_ZONE`**。

## Port already in use

改 `TS_PORT` in `config.env`，重新 `bootstrap.sh`，再 `close.sh` + `expose`。

## Route points to missing file

`status.sh` 显示 `⚠️ missing`。重新 `expose` 新路径，或 `close.sh <slug>`。

## Other tunnels on same account

本技能使用 **独立** 的 `TS_TUNNEL_NAME` 与本地 `config.yml`，不修改 Dashboard 上其他隧道或 Docker 容器，除非名称/hostname 冲突。

## Reset

```bash
bash scripts/close.sh
rm -f state/*.log
```

完全删除隧道：

```bash
source config.env
cloudflared tunnel delete "$TS_TUNNEL_NAME"
rm ~/.cloudflared/config.yml
```
