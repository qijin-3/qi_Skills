---
name: tunnel-serve
description: >-
  Expose local HTML files or folders to the public internet via a user-configured
  Cloudflare Tunnel subdomain. Use whenever the user wants to share local static
  content with a public URL: "把本地 HTML 暴露到公网", "临时分享这个网页",
  "tunnel serve", "share this html", "公开本地网页", "给页面一个网址",
  "expose local files", "cloudflare tunnel static site", or needs a temporary
  public link for local HTML/report folders. Works on any machine with any
  Cloudflare-managed domain — configuration lives in config.env (TS_ZONE,
  TS_SUBDOMAIN, TS_TUNNEL_NAME). If config is missing, help the user create it
  and explain how to obtain each value (Cloudflare account, zone, subdomain).
  Supports single files and folder directory listings; auto-shutdown after 1h
  by default.
---

# tunnel-serve

通过 **本机 Cloudflare Tunnel** 把本地 HTML/文件夹暴露到公网。
域名、子域名、隧道名等**全部在 `config.env` 维护**，技能本身不含任何用户专属域名。

公网 URL 形态：`https://<TS_SUBDOMAIN>.<TS_ZONE>/<slug>/`

- 单文件：`expose report.html` → `https://share.example.com/report/`
- 文件夹：`expose out/` → `https://share.example.com/out/`（目录列表）

## Agent 工作流（每次触发先走这里）

### 1. 检查配置

```bash
# 在技能目录下
test -f config.env && cat config.env || echo "MISSING"
```

若 `config.env` 不存在或不完整，**不要直接跑 expose/bootstrap**。先补齐配置。

### 2. 缺变量时询问用户（须说明如何获取）

读 `references/config-variables.md`，按下面模板问询：

| 变量 | 问用户什么 | 如何获取 |
|------|------------|----------|
| `TS_ZONE` | Cloudflare 根域名？ | 域名须已加入 [Cloudflare](https://dash.cloudflare.com/) 并完成 DNS 托管 |
| `TS_SUBDOMAIN` | 用哪个子域名对外？ | 自选未占用名，如 `share`、`preview` |
| `TS_TUNNEL_NAME` | 隧道名称？ | 可与子域名相同；账户内唯一 |

可选确认：`TS_PORT`（默认 8787）、`TS_DEFAULT_TTL`（默认 3600 秒）。

### 3. 写入 config.env

非交互（推荐 Agent）：

```bash
TS_ZONE=example.com TS_SUBDOMAIN=share TS_TUNNEL_NAME=share \
  bash scripts/init-config.sh
```

或交互：`bash scripts/init-config.sh`

### 4. 首次初始化隧道

若 `~/.cloudflared/config.yml` 不存在或用户从未 bootstrap：

```bash
bash scripts/bootstrap.sh
```

会安装 cloudflared、浏览器 login（选 `TS_ZONE`）、创建隧道、写 ingress、建 DNS。

### 5. 日常使用

```bash
bash scripts/expose.sh <file-or-folder> [custom-slug]
bash scripts/status.sh
bash scripts/close.sh [slug]    # 无 slug = 全停
bash scripts/extend.sh <minutes>  # 0 = 永不自动关
```

## Architecture

```
本机:
  serve.py (127.0.0.1:TS_PORT)  ←  cloudflared (tunnel TS_TUNNEL_NAME)
                                        │
                                        ▼
                          Cloudflare → https://TS_SUBDOMAIN.TS_ZONE
```

`serve.py` 仅监听 127.0.0.1；公网流量经 cloudflared 转发。

## 配置一览

所有可变项见 **`config.env`**（模板 `config.env.example`）：

| 变量 | 必填 | 说明 |
|------|------|------|
| `TS_ZONE` | ✓ | 根域名 |
| `TS_SUBDOMAIN` | ✓ | 子域名 |
| `TS_TUNNEL_NAME` | ✓ | cloudflared 隧道名 |
| `TS_PORT` | | 本地端口，默认 8787 |
| `TS_DEFAULT_TTL` | | 自动关闭秒数，默认 3600 |

派生：`TS_DOMAIN` = `${TS_SUBDOMAIN}.${TS_ZONE}`（脚本自动计算，勿手写）

详细说明 → `references/config-variables.md`

## 从旧版（硬编码域名）迁移

若技能曾写死某域名，在本机创建 `config.env` 即可，例如：

```bash
cat > config.env <<'EOF'
TS_ZONE=your-domain.com
TS_SUBDOMAIN=share
TS_TUNNEL_NAME=share
TS_PORT=8787
TS_DEFAULT_TTL=3600
EOF
```

已有 `~/.cloudflared` 凭证则通常无需重新 bootstrap；改 hostname 时需重跑 `bootstrap.sh`。

## References

- `references/config-variables.md` — 变量说明、获取方式、Agent 问询模板
- `references/setup-guide.md` — bootstrap 逐步说明
- `references/troubleshooting.md` — 连通性排查
