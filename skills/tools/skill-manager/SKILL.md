---
name: skill-manager
description: |
  管理 ~/.agents/skills 软链接与 ~/Skill Manager 本地技能库：从 GitHub 仓库选择性安装、覆盖更新、多设备配置、健康检查、换机路径修复。
  只要用户提到安装/卸载/更新技能、管理技能仓库、打开技能管理页面、检查软链接、换机迁移、修复路径、Skill Manager 或 ~/.agents/skills，就应使用本技能——即使用户没说「skill-manager」。
  触发词：安装技能、更新技能、管理技能仓库、技能管理页面、检查技能更新、清理软链接、同步技能、修复路径、换机。
---

# 技能管理器

统一管理 `~/Skill Manager`（本地数据）与 `~/.agents/skills`（默认软链接注册，与 skill-creator 一致）。初始化后 skill-manager 会安装到 `~/Skill Manager/<配置>/Skills/local/skill-manager/`，GUI 主页面为 `~/Skill Manager/index.html`（技能包内 `web/*.sample.html` 仅为模板）。

CLI 入口（`init` 完成后，与 skill-creator 相同）：

```bash
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py <command>
```

## 首次使用（Bootstrap）

```bash
python3 skills/tools/skill-manager/scripts/skill_manager.py init
```

`init` 会自动：

1. 创建工作区与设备配置
2. 将 skill-manager 复制到 Local 并创建 Agents 软链
3. 将 `web/index.sample.html` 部署为 `~/Skill Manager/index.html`

之后可通过 Finder 双击 `~/Skill Manager/Open Skill Manager.command` 启动服务并打开 GUI。

```
~/Skill Manager/
├── index.html                   # GUI 主页面（工作副本）
├── Open Skill Manager.command   # Mac 双击：启动服务 + 浏览器
├── <config-id>/
│   ├── config.json
│   └── Skills/
│       └── local/
│           └── skill-manager/   # 管理器本体（已软链到 ~/.agents/skills）
├── .cache/repos/
└── settings.json
```

## 换机 / 复制后修复路径

将整个 `~/Skill Manager` 或 `skill-manager` 文件夹复制到新电脑后，软链与启动器可能仍指向旧机器的绝对路径。运行：

```bash
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py fix-paths
```

若尚未完成 `init` 或软链不存在，可直接用仓库内脚本：

```bash
python3 path/to/skill-manager/scripts/skill_manager.py fix-paths
```

`fix-paths` 会：重建 `Open Skill Manager.command` 与 GUI、刷新 Local 中的 skill-manager 副本、按当前 `~/Skill Manager` 位置重连所有已同步技能的 `~/.agents/skills` 软链。

## 触发时第一步

每次使用本技能，先执行健康检查：

```bash
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py healthcheck
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
├── index.html
├── Open Skill Manager.command
├── <config-id>/
│   ├── config.json
│   └── Skills/
│       ├── local/
│       │   └── skill-manager/
│       └── <repo-slug>/
├── .cache/repos/

~/.agents/skills/
├── <skill-name> -> ~/Skill Manager/<config>/Skills/.../<skill-name>
```

## 多设备识别

优先级：`--device` 参数 → `SKILL_MANAGER_DEVICE` 环境变量 → `.active-device` 文件 → `devices.json` hostname 匹配 → 自动 sanitize(hostname)。

查看当前设备：

```bash
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py device current
```

## CLI 命令

```bash
# 初始化工作区
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py init

# 换机后修复路径
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py fix-paths

# 仓库
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py repo add owner/repo --branch main
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py repo list
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py repo remove owner/repo --purge

# 发现并安装
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py discover owner/repo
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py install owner/repo meeting
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py uninstall meeting

# 更新与状态
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py update
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py status

# Web GUI
python3 ~/.agents/skills/skill-manager/scripts/skill_manager.py ui
```

## 典型对话流程

**添加仓库并安装部分技能：**
1. `repo add <github-url>`
2. `discover <repo-id>` 列出可选技能
3. 用户选择后 `install <repo-id> <skill-name>`

**检查更新：**
1. `update` — 对所有已同步技能 fetch 并覆盖更新

**换机或复制 Skill Manager 后：**
1. `fix-paths` — 重建启动器与软链
2. `healthcheck` — 确认配置、目录与软链一致

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
