---
name: update-skills-docs
description: >
  自动扫描 skills/ 目录、维护 skills-sync.yaml、更新 README.md，
  并将 sync 组中的技能软链接到 ~/.claude/skills/ 注册到 Claude Code。
  当你在项目中增删改 skills、需要同步技能到本地 Claude Code、或更新公开技能列表时使用。
  也适用于用户说「更新 skills 文档」「同步技能」「注册技能到 claude」「刷新技能列表」。
---

# 更新 Skills 文档与 Claude Code 同步

你是 qi_Skills 项目的技能配置管理员。当用户执行 `/update-skills-docs` 时，完成以下三件事：

1. **维护 skills-sync.yaml** — 扫描 `skills/` 下所有技能，更新 `sync` / `unsync` 两组
2. **更新 README** — 展示完整技能目录树与分组列表（精简摘要，标注已同步技能）
3. **同步到 Claude Code** — 将 `sync` 组中的技能软链接到 `~/.claude/skills/`，并清理已取消同步的链接

## 快速执行

优先运行仓库脚本（推荐）：

```bash
cd <repo-root>
python3 scripts/skills-registry.py all
```

子命令：
- `scan` — 仅扫描并更新 `skills-sync.yaml`
- `readme` — 仅更新 README.md
- `sync` — 仅执行 Claude Code 软链接同步
- `all` — 全部执行

如果脚本不可用，按下方手动步骤执行等效操作。

## 执行步骤

### 1. 扫描 skills/ 目录

递归查找所有 `SKILL.md`，排除：
- `deprecated/`
- `node_modules/`
- `template/`（游记模板内的占位文件）

注意嵌套结构：技能可能位于 `skills/travel_journal/travel-journal/` 等子目录中。

### 2. 更新 skills-sync.yaml

配置文件：`skills-sync.yaml`（仓库根目录，**用户手动编辑 sync / unsync**）

对每个发现的技能：
- 从 SKILL.md frontmatter 提取 `name` 和 `description`
- 新技能默认加入 `unsync`
- 已删除技能从两组移除
- 保留用户在两组间的分配（支持复制粘贴移动）

### 3. 同步到 Claude Code

仅对 `sync` 组中的技能创建软链接：

```bash
ln -sfn <绝对路径/技能目录> ~/.claude/skills/<name>
```

规则：
- 链接名使用 frontmatter 的 `name`，不是目录名
- 技能从 `sync` 移到 `unsync` 时，**必须移除**指向本仓库的软链接
- 扫描 `~/.claude/skills/`，清理所有指向本仓库但不在 sync 组的残留链接
- 检测 `~/.claude/skills` 是否是指向本仓库的符号链接，若是则报错退出

### 4. 更新 README.md

找到 `## Skills 目录` 部分，展示**全部技能**：

1. **目录树** — `skills/` 文件夹结构，每行附一句话摘要，`[已同步]` 标注
2. **分组列表** — 按 `product design`、`travel_journal` 等分组

### 5. 输出变更摘要

报告：
- 技能总数 / sync 组数量
- 新技能、移除、sync ↔ unsync 的移动
- 新链接 / 移除的软链接

## 同步配置手动编辑

在 `skills-sync.yaml` 的 `sync` / `unsync` 之间移动 name：

```yaml
sync:
  - idea-validator
  - meeting

unsync:
  - travel-journal
```

完整格式说明见 [references/registry-format.md](./references/registry-format.md)。

## 注意事项

- 保持 README.md 的其他内容不变
- README 使用精简摘要，完整描述留在各 `SKILL.md`
- 运行 `sync` 前确认 `skills-sync.yaml` 符合用户意图
