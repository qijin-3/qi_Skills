---
name: update-skills-docs
description: >
  自动扫描 skills/ 目录并更新 README.md 技能目录树与分组列表。
  当你在项目中增删改 skills、或需要刷新公开技能列表时使用。
  也适用于用户说「更新 skills 文档」「刷新技能列表」「更新 README 技能目录」。
---

# 更新 Skills 文档

你是 qi_Skills 项目的技能文档管理员。当用户执行 `/update-skills-docs` 时：

1. **扫描 skills/ 目录** — 递归查找所有 `SKILL.md`
2. **更新 README.md** — 刷新 `## Skills 目录` 部分的目录树与分组列表

不需要创建软链接，也不需要同步到 `~/.claude/skills/`、`~/.agent/skills/` 等本地目录。

## 快速执行

优先运行仓库脚本（推荐）：

```bash
cd <repo-root>
python3 scripts/skills-registry.py readme
```

如果脚本不可用，按下方手动步骤执行等效操作。

## 执行步骤

### 1. 扫描 skills/ 目录

递归查找所有 `SKILL.md`，排除：

- `deprecated/`
- `node_modules/`
- `template/`（游记模板内的占位文件）

注意嵌套结构：技能可能位于 `skills/travel_journal/travel-journal/` 等子目录中。

对每个发现的技能，从 SKILL.md frontmatter 提取 `name` 和 `description`，生成精简摘要（description 首句，≤80 字）。

### 2. 更新 README.md

找到 `## Skills 目录` 部分，展示**全部技能**：

1. **目录树** — `skills/` 文件夹结构，每行附一句话摘要
2. **分组列表** — 按 `product`、`design`、`travel_journal` 等分组，每项链接到 `./skills/.../SKILL.md`

### 3. 输出变更摘要

报告：

- 技能总数
- 新发现的技能
- 已删除的技能

## 注意事项

- 保持 README.md 的其他内容不变
- README 使用精简摘要，完整描述留在各 `SKILL.md`
- 技能安装由用户通过 Agent 或手动复制完成，本技能不负责本地注册
