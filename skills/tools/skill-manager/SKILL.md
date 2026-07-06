---
name: skill-manager
description: |
  管理 ~/.agent/skills 软链接与 ~/Skill Manager 本地技能库：从 GitHub 仓库选择性安装、覆盖更新、多设备配置、健康检查。
  只要用户提到安装/卸载/更新技能、管理技能仓库、打开技能管理页面、检查软链接、Skill Manager 或 ~/.agent/skills，就应使用本技能——即使用户没说「skill-manager」。
  触发词：安装技能、更新技能、管理技能仓库、技能管理页面、检查技能更新、清理软链接、同步技能。
---

# 技能管理器

统一管理 `~/Skill Manager`（本地数据）与 `~/.agent/skills`（软链接注册）。已安装技能存放在 `~/Skill Manager/Skills/`。skill-manager 自身保留在仓库 / `~/.agent/skills/skill-manager`，不放入 Skill Manager 目录。

## 首次使用（Bootstrap）

skill-manager 代码不复制到 Skill Manager 目录，只需注册软链：

```bash
mkdir -p ~/.agent/skills
ln -sf <技能源路径>/skill-manager ~/.agent/skills/skill-manager
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py init
```

技能源路径示例：克隆的 `qi_Skills/skills/tools/skill-manager`。

`init` 会自动创建：

```
~/Skill Manager/
├── Open Skill Manager.html      # 双击：检测服务并打开 GUI
├── Open Skill Manager.command   # Mac 双击：启动服务 + 浏览器
├── configs/<device-id>.json
├── .cache/repos/
└── Skills/                      # 已安装技能
```

之后可通过 Finder 打开 `~/Skill Manager/Open Skill Manager.html` 或 `.command` 使用。

## 触发时第一步

每次使用本技能，先执行健康检查：

```bash
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py healthcheck
```

## 双入口

| 用户意图 | 操作 |
|----------|------|
| 打开管理页面 / GUI | 双击 `~/Skill Manager/Open Skill Manager.command`，或 `python3 ... skill_manager.py ui` |
| 命令行操作 | 见下方命令表 |

GUI 默认 `http://127.0.0.1:8791/`，支持增删仓库、勾选同步技能、检查更新。

## 目录结构

```
~/Skill Manager/
├── Open Skill Manager.html
├── Open Skill Manager.command
├── configs/
│   ├── devices.json          # hostname → device-id 映射（可选）
│   └── <device-id>.json      # 当前设备的仓库与技能配置
├── .cache/repos/             # git 浅克隆缓存
└── Skills/
    └── <skill-name>/         # 已安装技能

~/.agent/skills/
├── skill-manager -> <仓库路径>/skill-manager   # 管理器自身，不在 Skills 下
└── <skill-name> -> ~/Skill Manager/Skills/<skill-name>
```

## 多设备识别

优先级：`--device` 参数 → `SKILL_MANAGER_DEVICE` 环境变量 → `.active-device` 文件 → `devices.json` hostname 匹配 → 自动 sanitize(hostname)。

查看当前设备：

```bash
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py device current
```

## CLI 命令

```bash
# 初始化工作区
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py init

# 仓库
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py repo add owner/repo --branch main
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py repo list
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py repo remove owner/repo --purge

# 发现并安装
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py discover owner/repo
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py install owner/repo meeting
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py uninstall meeting

# 更新与状态
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py update
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py status

# Web GUI
python3 ~/.agent/skills/skill-manager/scripts/skill_manager.py ui
```

## 典型对话流程

**添加仓库并安装部分技能：**
1. `repo add <github-url>`
2. `discover <repo-id>` 列出可选技能
3. 用户选择后 `install <repo-id> <skill-name>`

**检查更新：**
1. `update` — 对所有已同步技能 fetch 并覆盖更新

**用户删了本地技能文件夹：**
1. `healthcheck` — 自动清理断裂软链

## 安全

- `repo remove --purge` 和 `uninstall` 前确认用户意图
- 技能名冲突时拒绝安装并说明来源仓库
- 仅支持 GitHub 仓库

## 参考

| 场景 | 读取 |
|------|------|
| 配置文件字段 | `references/manifest-schema.md` |
| 多设备注册 | `references/devices-schema.md` |
