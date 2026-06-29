# 服务器状态

> 最后更新：2026-06-10

## 服务器规格

- **IP**: 106.15.43.99
- **域名**: biteof.top
- **CPU**: 2 vCPU (Intel Xeon Platinum)
- **内存**: 1.6 GB（无 Swap）
- **磁盘**: 40 GB
- **系统**: Alibaba Cloud Linux
- **Docker**: 29.2.1 + Compose v5.0.2
- **Docker 镜像源**: docker.1ms.run, docker.xuanyuan.me（`/etc/docker/daemon.json`）

## 当前运行服务

| 服务 | 镜像 | 域名 | 内存占用 | 用途 |
|------|------|------|---------|------|
| Nginx | nginx:alpine | https://biteof.top | ~12 MB | 反向代理 + 主域名占位页（80/443） |
| Vaultwarden | vaultwarden/server:latest | https://vault.biteof.top | ~74 MB | 密码管理器 |
| RSSHub | diygod/rsshub:latest | https://rsshub.biteof.top | ~265 MB | RSS 源生成器 |
| Redis | redis:alpine | - | ~11 MB | RSSHub 缓存 |
| Certbot | certbot/certbot | - | ~4 MB | SSL 证书自动续期 |

**容器总内存**: ~362 MB / 1.6 GB

## 资源使用

- **内存**: 已用 ~881 MB，可用 ~731 MB
- **磁盘**: 已用 4.9 GB / 40 GB (13%)

## 域名与 SSL

| 子域名 | 指向服务 | SSL 证书路径 |
|--------|---------|-------------|
| biteof.top / www.biteof.top | 占位页（显示当前时间） | /etc/letsencrypt/live/biteof.top/ |
| vault.biteof.top | vaultwarden:80 | /etc/letsencrypt/live/vault.biteof.top/ |
| rsshub.biteof.top | rsshub:1200 | /etc/letsencrypt/live/rsshub.biteof.top/ |

注：443 端口的 `default_server` 已设置为 biteof.top 占位页，未匹配子域名的 HTTPS 请求不再回退到 Vaultwarden。

所有 SSL 证书由 Let's Encrypt 签发，certbot 容器自动续期。

## 关键配置文件

- `/opt/services/docker-compose.yml` — 所有服务定义
- `/opt/services/.env` — 环境变量（密码、token 等）
- `/opt/services/nginx/conf.d/default.conf` — Nginx 路由配置
- `/opt/services/nginx/html/index.html` — biteof.top 主域名占位页（中央显示当前时间）

## .env 中的变量

- `VAULTWARDEN_ADMIN_TOKEN` — Vaultwarden 管理后台 token

## RSSHub 特殊配置

- 小红书 Cookie 已配置（XIAOHONGSHU_COOKIE）
- 路由缓存 30 分钟（CACHE_ROUTE_EXPIRE=1800）
- 内容缓存 2 小时（CACHE_CONTENT_EXPIRE=7200）

## 阿里云安全组

已开放端口：TCP 22, 80, 443

## 操作记录

- 2026-06-10: 清理未使用的 Docker 卷（删除 3 个悬空卷），检查服务器状态，所有服务正常运行（nginx、vaultwarden、rsshub、redis、certbot），当前磁盘使用 5.1GB/40GB (14%)，内存已用 909MB/1.6GB
- 2026-04-29: 主域名 biteof.top 配置占位页（显示当前时间），申请 Let's Encrypt 证书（含 www.biteof.top），新增 nginx html 卷挂载，443 default_server 指向占位页
- 2026-04-09: 移除 WeWe RSS，回收 ~121 MB 镜像 + 数据目录
- 2026-04-07: 部署 WeWe RSS（SQLite 版），配置 wewe.biteof.top
- 2026-04-06: 移除 Miniflux、Miniflux-AI、PostgreSQL，回收 ~158 MB 磁盘
- 2026-03-13: RSSHub 添加小红书 Cookie 和缓存策略
- 2026-03-09: RSSHub 配置子域名 rsshub.biteof.top
- 2026-03-09: 本地 Miniflux 数据库迁移到服务器
- 2026-03-08: Vaultwarden、RSSHub 更新到最新版
- 2026-03-06: ICP 备案完成，配置 HTTPS（vault/rss 子域名）
- 2026-02-23: 初始部署 Nginx + Vaultwarden + Miniflux + PostgreSQL + RSSHub + Redis
