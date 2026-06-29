# 部署方案与脚本参考

生成部署文档与脚本时使用。项目目录约定：`/opt/<仓库名>`（仓库名由 clone URL 推断）。

## 文档结构

- **第 0 步**：已填入 ECS IP、仓库 URL、SSH 用户、可选域名与 SSL 邮箱；后续命令全部使用这些值。
- **SSH 首次部署**：登录 → 克隆 →（可选）.env → `bash deploy/start.sh` → 安全组放行端口 → 验证。停止：`bash deploy/stop.sh`。
- **start/stop 两种用法**：SSH 直接执行；阿里云应用管理时将两文件**完整内容**粘贴到「应用启动脚本」「应用停止脚本」。

## start.sh 要点

- **代码目录**：优先 `SCRIPT_DIR/..`（若含 package.json）；否则当前目录 → `code_deploy_application` → `find package.json`（maxdepth 2）。
- **Node**：未安装则按 os-release 用 yum/apt 安装 Node 20。
- **PM2**：未安装则 `npm install -g pm2`。
- **依赖与构建（必做）**：
  - 有 yarn.lock 且系统有 yarn → `yarn install`（或 `--frozen-lockfile`）→ `yarn build`
  - 有 yarn.lock 但无 yarn → 提示后 `npm ci`/`npm install` → `npm run build`
  - 无 yarn.lock → `npm ci`/`npm install` → `npm run build`
- **启动**：有 ecosystem.config.js 则 `pm2 start ecosystem.config.js`；否则按项目类型（静态：`npx serve dist -s -l <端口>`；Node：`pm2 start npm --name "<应用名>" -- start` 等）。应用名与 stop.sh 一致。

## stop.sh 要点

- PM2：`pm2 stop <应用名>` → `pm2 delete <应用名>`。无 PM2 时用 `ps`/`pkill` 清理。

## update.sh

- 逻辑：`cd 项目根` → `git pull` → `bash deploy/start.sh`。供手动与 GitHub Actions 共用。
- 调用：`bash /opt/<项目目录名>/deploy/update.sh`。

## 端口与安全组

- 端口以 ecosystem.config.js / package.json / Dockerfile 为准。安全组：应用端口；可选 22；绑域名则 80、443。

## 环境变量

- 在控制台或服务器 .env 配置；文档只列变量名与用途。前端仅暴露非敏感配置（VITE_* / REACT_APP_* / NEXT_PUBLIC_*）。

## 域名与 HTTPS（可选）

- DNS：@ 与 www 的 A 记录指向 ECS IP。安全组放行 80、443。
- 服务器：Nginx + Certbot；`proxy_pass http://127.0.0.1:<应用端口>`；`certbot --nginx -d <域名> -d www.<域名> --redirect`。
- 脚本：`deploy/setup-domain-ssl.sh`、`deploy/nginx-<域名主名>.conf`（HTTP 块，certbot 加 HTTPS）。证书邮箱更新：`certbot update_account --email 新邮箱`。

## 故障排查

| 现象 | 处理 |
|------|------|
| 找不到 package.json | start.sh 用脚本路径→工作目录→code_deploy_application→find 查找 |
| Node 未安装 | 脚本内安装 Node 20 或手动 yum/apt |
| yarn: command not found | start.sh 中 yarn.lock 存在时需无 yarn 则用 npm |
| 依赖慢/失败 | npm config set registry https://registry.npmmirror.com |
| 构建失败 | 查环境变量、pm2 logs |
| 端口占用 | lsof -i :<端口>，停进程或改端口 |
| 外网不可访问 | 安全组、防火墙、监听 0.0.0.0 |
| Nginx sites-enabled 不存在 | mkdir -p /etc/nginx/sites-enabled，再 ln -sf |
| deploy/update.sh: No such file | workflow 先 `git pull` 或 `git fetch && git reset --hard origin/main` 再执行 update.sh；或服务器上先手动 git pull 一次 |
| git pull 报 could not read Username | 服务器改用 SSH 远程 + Deploy Key（见上方「服务器 git 拉取配置」），Key 填 .pub 公钥整行 |
| git pull 报 local changes would be overwritten | workflow 用 `git fetch origin && git reset --hard origin/main` 再执行 update.sh，部署机以远程为准 |

## GitHub Actions

- **Secrets**：DEPLOY_HOST、DEPLOY_USER、DEPLOY_SSH_KEY（服务器专用于「GitHub 登录到 ECS」的 SSH 私钥全文）。
- **服务器登录用密钥（一次性）**：`ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""`，`cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys`，私钥复制到 GitHub Secrets 的 DEPLOY_SSH_KEY；**勿将私钥贴到聊天或公开处**。
- **服务器 git 拉取配置（一次性，必做）**：若仓库用 HTTPS 远程，Actions 里执行 `git pull` 会报 `could not read Username for 'https://github.com'`（非交互无法输入密码）。必须在服务器上改为 **SSH 远程 + Deploy Key**：
  1. 服务器生成专用于拉代码的密钥：`ssh-keygen -t ed25519 -f ~/.ssh/github_deploy_key -N ""`；`cat ~/.ssh/github_deploy_key.pub` 复制公钥。
  2. 仓库 Settings → Deploy keys → Add deploy key，Title 如 `ECS pull`，Key 粘贴公钥（**Key 字段填 .pub 的整行**），只读即可。
  3. 服务器：`cd /opt/<项目目录名> && git remote set-url origin git@github.com:<用户>/<仓库>.git`。
  4. 服务器配置 SSH 用该密钥访问 GitHub：`~/.ssh/config` 增加 Host github.com、User git、IdentityFile ~/.ssh/github_deploy_key、IdentitiesOnly yes；`chmod 600 ~/.ssh/config`。
  5. 可选：`ssh-keyscan github.com >> ~/.ssh/known_hosts` 避免首次连接询问 yes/no。
- **工作流脚本（推荐）**：`cd /opt/<项目目录名> && git fetch origin && git reset --hard origin/main && bash deploy/update.sh`。用 **fetch + reset --hard** 而不仅 `git pull`，避免服务器上有本地修改时出现 `Your local changes would be overwritten by merge` 导致部署失败；部署机应以远程为准、丢弃本地改动。
- 分支名若非 main：将 `origin/main` 改为 `origin/<分支名>`。
