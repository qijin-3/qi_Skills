---
name: ali-deploy-guide-generator
description: 根据项目技术栈生成阿里云 ECS 部署方案与 GitHub 自动化部署配置。生成前先收集 ECS IP、仓库 URL、SSL 邮箱等一次性信息并做部署前敏感信息检查；支持 SSH 首次部署、域名 HTTPS、推送后自动部署。在用户要求「部署方案」「阿里云部署」「GitHub 自动化部署」或「根据部署配置指南生成部署」时使用。
---

# 阿里云 ECS 部署指南生成

通用流程：**0. 信息收集** → **0.5 部署前敏感信息检查** → **1. 分析项目** → **2. 生成方案与脚本** → **3. GitHub Actions**。适用任意 Node 前端/全栈（Vite、Next、Nuxt、CRA、纯静态等）。

---

## 0. 信息收集（第一步）

在生成任何部署文档或脚本之前，向用户收集下表信息，写入部署文档「第 0 步」，后续所有命令用这些值替换，用户复制即用。

| 项 | 说明 | 示例/默认 |
|----|------|-----------|
| ECS 公网 IP | 阿里云 ECS 实例公网 IP | `8.153.111.173` |
| 仓库 URL | GitHub/GitLab 克隆地址 | 可从 `git remote -v` 推断后请用户确认 |
| SSH 用户 | 登录 ECS 的用户名 | `root` |
| SSL 邮箱（可选） | Let's Encrypt 证书过期提醒 | 用户邮箱 |
| 域名（可选） | 要绑定的主域名（可含 www） | `example.com` |

文档开头写「第 0 步：已填入你的信息」，列出上述项；命令中 IP、仓库 URL、项目路径（由仓库名推断）、SSL 邮箱、域名全部替换。未提供域名/SSL 邮箱时，域名小节可用占位说明。

---

## 0.5 部署前敏感信息检查

在写入部署相关文件之前，对当前仓库做一次通用检查。检查项、搜索模式与输出形式见 **references/security-check.md**。输出：通过 / 需注意 / 需修复；有需修复时先给修改建议再继续生成。

---

## 1. 分析项目

识别：package.json（框架、Node 版本、build/start 脚本、包管理 yarn/npm/pnpm）；运行方式（ecosystem.config.js、Dockerfile、端口、静态/Node）；外部服务（Supabase、Redis、DB 等）；deploy/ 是否已有 start.sh、stop.sh、update.sh。记录框架、端口、包管理器、环境变量需求。

---

## 2. 生成部署方案与脚本

基于 **references/deploy.md** 与项目分析结果生成部署文档与脚本。

- **第 0 步**：用已收集信息写「已填入你的信息」。
- **SSH 首次部署**：登录 → 克隆 →（可选）.env → `bash deploy/start.sh` → 安全组 → 验证。停止：`bash deploy/stop.sh`。说明 start/stop 的两种用法（SSH 执行 + 阿里云控制台粘贴）。
- **start.sh / stop.sh**：已有则引用并检查 yarn 缺失时是否回退 npm（见 references/deploy.md）；无则按 reference 模板生成，**必须**含 yarn.lock 无 yarn 时用 npm。
- **update.sh**：提供 `git pull` + `bash deploy/start.sh`，文档写更新后执行 `bash /opt/<项目目录名>/deploy/update.sh`。
- **端口与安全组**：明确端口；说明放行该端口及可选 80/443。
- **环境变量**：列变量名与用途，不写密钥。
- **域名与 HTTPS**：用户已提供域名与 SSL 邮箱则命令中直接使用；未提供则小节保留、命令用占位。
- **验证与故障排查**：简要步骤；常见问题见 references/deploy.md 故障排查表。

---

## 3. GitHub Actions

- **CI**：push/PR 到目标分支 → checkout → 安装 Node → 安装依赖 → build。
- **Deploy**：push 到 main → SSH 到 ECS → 执行 `cd /opt/<项目目录名> && git fetch origin && git reset --hard origin/main && bash deploy/update.sh`。用 **fetch + reset --hard** 避免服务器本地修改导致「local changes would be overwritten」；分支非 main 时改为 `origin/<分支名>`。Secrets：DEPLOY_HOST、DEPLOY_USER、DEPLOY_SSH_KEY。文档写清：① 服务器登录用密钥（github_deploy → authorized_keys，私钥 → GitHub Secrets）；② **服务器 git 拉取配置**（SSH 远程 + Deploy Key，否则 Actions 里 git 会报 could not read Username）；提醒勿将私钥贴到聊天或公开处。详见 **references/deploy.md** GitHub Actions 与故障排查。

---

## 输出清单

1. 部署前检查结论（通过/需注意/需修复）。
2. 部署方案 Markdown（含第 0 步、SSH 首次部署、start/stop/update、端口、环境变量、可选域名 HTTPS、验证与故障排查）。可保存为 `deploy/部署方案-阿里云.md`。
3. 脚本：deploy/start.sh、deploy/stop.sh、deploy/update.sh；若用户提供域名与 SSL 邮箱则增加 deploy/setup-domain-ssl.sh 与 deploy/nginx-<域名主名>.conf。
4. GitHub Actions：CI + Deploy 工作流；文档说明 Secrets 与 SSH 密钥配置。
5. 简短说明：端口、运行方式、「第一次 SSH 执行 start.sh；后续 push 自动部署或手动 update.sh」。
