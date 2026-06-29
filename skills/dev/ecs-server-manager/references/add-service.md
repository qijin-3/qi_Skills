# 添加新服务

## 前置检查

```bash
# 检查当前资源
ssh root@106.15.43.99 'free -h && df -h / && docker stats --no-stream --format "{{.Name}}\t{{.MemUsage}}"'
```

服务器仅 1.6GB 内存无 Swap，评估新服务内存需求是否可承受。如资源不足，建议：
- 添加 2GB Swap：`ssh root@106.15.43.99 'fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && echo "/swapfile swap swap defaults 0 0" >> /etc/fstab'`
- 或升配服务器

## 步骤 1：编辑 docker-compose.yml

在本地编辑 `/tmp/docker-compose-ecs.yml`（保持与服务器 `/opt/services/docker-compose.yml` 同步），添加新服务定义。

原则：
- 优先使用 SQLite 而非 MySQL/PostgreSQL（节省内存）
- 使用 `restart: unless-stopped`
- 敏感值用 `${VAR_NAME}` 引用 .env 文件
- 如需持久化，用 volumes 或 bind mount

添加后上传：
```bash
scp /tmp/docker-compose-ecs.yml root@106.15.43.99:/opt/services/docker-compose.yml
```

如有新的环境变量，追加到 .env：
```bash
ssh root@106.15.43.99 "echo 'NEW_VAR=value' >> /opt/services/.env"
```

## 步骤 2：启动容器

```bash
ssh root@106.15.43.99 'cd /opt/services && docker compose up -d <service-name>'
```

## 步骤 3：配置域名（子域名模式）

1. **DNS**：用户在阿里云 DNS 控制台添加 A 记录
   - 主机记录：`<subdomain>`
   - 记录值：`106.15.43.99`

2. **Nginx HTTP 配置**：先添加仅 HTTP 的 server block（用于 certbot 验证）
   Nginx 配置文件：`/opt/services/nginx/conf.d/default.conf`

3. **SSL 证书申请**：
```bash
ssh root@106.15.43.99 'docker run --rm \
  -v /opt/services/certbot/www:/var/www/certbot \
  -v /opt/services/certbot/conf:/etc/letsencrypt \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d <subdomain>.biteof.top --email admin@biteof.top --agree-tos --no-eff-email'
```

4. **Nginx HTTPS 配置**：添加完整的 HTTP redirect + HTTPS server block

```nginx
# <ServiceName> - <subdomain>.biteof.top (HTTP -> HTTPS redirect)
server {
    listen 80;
    server_name <subdomain>.biteof.top;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# <ServiceName> - <subdomain>.biteof.top (HTTPS)
server {
    listen 443 ssl;
    server_name <subdomain>.biteof.top;

    ssl_certificate /etc/letsencrypt/live/<subdomain>.biteof.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<subdomain>.biteof.top/privkey.pem;

    location / {
        proxy_pass http://<container-name>:<port>;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. **上传并重载 Nginx**：
```bash
scp /tmp/nginx-default.conf root@106.15.43.99:/opt/services/nginx/conf.d/default.conf
ssh root@106.15.43.99 'docker exec nginx nginx -t && docker exec nginx nginx -s reload'
```

## 步骤 4：验证

```bash
curl -s -o /dev/null -w "%{http_code}" https://<subdomain>.biteof.top/
```

## 步骤 5：更新技能文档

编辑 `references/server-state.md`：
- 在「当前运行服务」表格中添加新服务
- 在「域名与 SSL」表格中添加新域名
- 在「操作记录」中添加本次操作
- 更新资源使用数据和「最后更新」日期

## 注意事项

- 因国内 Docker Hub 访问受限，服务器配有镜像加速（docker.1ms.run）
- 所有子域名需已完成 ICP 备案（biteof.top 已备案）
- cookie 或含特殊字符的环境变量，避免用 heredoc，改用本地写文件 + scp 上传
