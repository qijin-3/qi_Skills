# 配置变量说明

所有与域名、隧道、端口相关的值集中在技能根目录的 **`config.env`**（不入库）。
模板见 `config.env.example`。

## 必填变量

| 变量 | 含义 | 如何获取 / 配置 |
|------|------|-----------------|
| `TS_ZONE` | Cloudflare 根域名（Zone） | 域名须已添加到 [Cloudflare](https://dash.cloudflare.com/) 并完成 DNS 托管。Dashboard → **网站** → **添加站点**。登录 `cloudflared tunnel login` 时须选择此 Zone。 |
| `TS_SUBDOMAIN` | 对外子域名 | 自选未被占用的名称，如 `share`、`preview`。公网 URL 为 `https://<TS_SUBDOMAIN>.<TS_ZONE>/<slug>/`。须在 Cloudflare DNS 中可创建 CNAME（bootstrap 会自动创建）。 |
| `TS_TUNNEL_NAME` | cloudflared 隧道名 | 账户内唯一，建议与 `TS_SUBDOMAIN` 相同。由 `bootstrap.sh` 执行 `cloudflared tunnel create` 创建。 |

**派生值**（无需手写）：`TS_DOMAIN` = `${TS_SUBDOMAIN}.${TS_ZONE}`

## 可选变量

| 变量 | 默认 | 含义 |
|------|------|------|
| `TS_PORT` | `8787` | 本地路由 `serve.py` 端口；须与 `~/.cloudflared/config.yml` 中 ingress 一致。冲突时用 `lsof -nP -iTCP:8787 -sTCP:LISTEN` 排查。 |
| `TS_DEFAULT_TTL` | `3600` | 首次 `expose` 后自动关闭秒数（1 小时）。`extend.sh 0` 可改为永不自动关。 |
| `TS_CF_HOME` | `~/.cloudflared` | cloudflared 证书与隧道凭证目录。 |
| `TS_CF_CONFIG` | `$TS_CF_HOME/config.yml` | 本地 ingress 配置；`bootstrap.sh` 会写入。 |

## 创建 config.env

**交互式**（推荐首次使用）：

```bash
bash scripts/init-config.sh
```

**非交互**（Agent / CI）：

```bash
TS_ZONE=example.com TS_SUBDOMAIN=share TS_TUNNEL_NAME=share \
  bash scripts/init-config.sh
```

**手动**：

```bash
cp config.env.example config.env
# 编辑 TS_ZONE、TS_SUBDOMAIN、TS_TUNNEL_NAME
```

## 前置条件检查清单

1. **Cloudflare 账户** — 免费版即可。
2. **域名在 Cloudflare** — `TS_ZONE` 对应站点状态为 Active。
3. **cloudflared** — macOS: `brew install cloudflared`；或由 `bootstrap.sh` 安装。
4. **config.env** — 三台必填变量已填。
5. **bootstrap 已完成** — `~/.cloudflared/cert.pem`、隧道凭证、`config.yml`、DNS CNAME 存在。

验证：

```bash
bash scripts/status.sh
```

## 修改配置后

| 改了什么 | 需要做什么 |
|----------|------------|
| `TS_ZONE` / `TS_SUBDOMAIN` | 更新 `config.env` 后重新 `bootstrap.sh`（会更新 DNS 与 ingress） |
| `TS_TUNNEL_NAME` | 重新 `bootstrap.sh`（可能创建新隧道） |
| `TS_PORT` | 更新 `config.env`，重新 `bootstrap.sh` 写 ingress，重启：`close.sh` 再 `expose` |
| 仅换机器 | 复制或重建 `config.env`；cloudflared 凭证在 `~/.cloudflared`，新机器需重新 login + bootstrap |

## Agent 缺变量时的问询模板

向用户确认时，附带获取方式：

1. **TS_ZONE** — 「你的域名是否已在 Cloudflare？根域名是什么（如 `example.com`）？」
2. **TS_SUBDOMAIN** — 「希望用哪个子域名对外分享（如 `share`）？需未被其他服务占用。」
3. **TS_TUNNEL_NAME** — 「cloudflared 隧道名称（可与子域名相同，账户内唯一）。」

凑齐后写入 `config.env`，再引导运行 `bootstrap.sh`（若尚未初始化）。
