---
name: ecs-server-manager
description: 阿里云 ECS 服务器运维管理工具。管理部署在 106.15.43.99 (biteof.top) 上的自托管服务。当用户提到「服务器」「ECS」「部署服务」「移除服务」「服务器状态」「biteof.top」，或要求检查/添加/删除/更新服务器上的服务时使用此技能。也适用于 SSL 证书管理、Nginx 配置、Docker 容器管理、域名配置等服务器运维操作。
---

# ECS Server Manager

管理部署在阿里云 ECS 上的自托管服务集群。

## 服务器连接

```bash
ssh root@106.15.43.99
```

- SSH 密钥认证已配置（`~/.ssh/id_ed25519`），无需密码
- 所有服务文件位于 `/opt/services/`
- 配置文件：`docker-compose.yml`、`.env`、`nginx/conf.d/default.conf`

## 核心操作流程

执行任何服务器操作前，先读取 `references/server-state.md` 获取当前服务器状态（服务列表、资源占用、域名映射等）。

### 添加新服务

读取 `references/add-service.md` 获取完整步骤。简要流程：
1. 检查服务器资源是否充足
2. 在 docker-compose.yml 中添加服务定义
3. 添加 DNS A 记录 → 申请 SSL 证书 → 配置 Nginx
4. 启动服务并验证
5. **更新 `references/server-state.md`**

### 移除服务

读取 `references/remove-service.md` 获取完整步骤。简要流程：
1. 停止并删除容器
2. 从 docker-compose.yml 中移除服务定义
3. 从 Nginx 配置中移除对应路由
4. 清理数据卷和旧镜像
5. **更新 `references/server-state.md`**

### 检查服务器状态

```bash
ssh root@106.15.43.99 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" && echo "---" && free -h && echo "---" && df -h /'
```

### 更新服务

```bash
ssh root@106.15.43.99 'cd /opt/services && docker compose pull <service> && docker compose up -d <service> && docker image prune -f'
```

## 自更新规则

每次对服务器上的服务进行增删改操作后，必须更新 `references/server-state.md`，确保以下信息准确：
- 当前运行的服务列表及其镜像版本
- 每个服务的域名和访问地址
- 最近一次操作记录
- 资源使用概况

更新方法：执行状态检查命令获取实时数据，然后编辑 `references/server-state.md`。
