# 移除服务

## 步骤 1：停止并删除容器

```bash
ssh root@106.15.43.99 'cd /opt/services && docker compose stop <service> && docker compose rm -f <service>'
```

如果服务有依赖的基础设施容器（如专用数据库），一并移除：
```bash
ssh root@106.15.43.99 'cd /opt/services && docker compose stop <db-service> && docker compose rm -f <db-service>'
```

## 步骤 2：编辑 docker-compose.yml

从 docker-compose.yml 中删除该服务的定义，以及关联的 volumes 声明。
本地编辑后上传：
```bash
scp /tmp/docker-compose-ecs.yml root@106.15.43.99:/opt/services/docker-compose.yml
```

同时清理 .env 中不再需要的变量。

## 步骤 3：更新 Nginx 配置

从 `/opt/services/nginx/conf.d/default.conf` 中移除该服务对应的：
- HTTP → HTTPS redirect server block
- HTTPS server block
- default server 中的 location block（如有）

上传并重载：
```bash
scp /tmp/nginx-default.conf root@106.15.43.99:/opt/services/nginx/conf.d/default.conf
ssh root@106.15.43.99 'docker exec nginx nginx -t && docker exec nginx nginx -s reload'
```

## 步骤 4：清理资源

```bash
# 删除孤立数据卷
ssh root@106.15.43.99 'docker volume rm <volume-name>'

# 清理未使用的镜像
ssh root@106.15.43.99 'docker image prune -a -f'
```

## 步骤 5：验证

```bash
# 确认容器已移除
ssh root@106.15.43.99 'docker ps --format "{{.Names}}"'

# 检查释放的内存
ssh root@106.15.43.99 'free -h'
```

## 步骤 6：更新技能文档

编辑 `references/server-state.md`：
- 从「当前运行服务」表格中删除该服务
- 从「域名与 SSL」表格中删除对应域名
- 在「操作记录」中添加本次移除操作
- 更新资源使用数据和「最后更新」日期

## DNS 记录

移除服务后，可选择保留或删除 DNS A 记录（在阿里云 DNS 控制台操作）。
SSL 证书可保留（certbot 会在续期时自动跳过无效域名）。
