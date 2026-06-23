---
name: update-skills-docs
description: >
  自动扫描 skills/ 目录、维护技能注册表（skills-registry.yaml）、更新 README.md，
  并将标记为 sync 的技能软链接到 ~/.claude/skills/ 注册到 Claude Code。
  当你在项目中增删改 skills、需要同步技能到本地 Claude Code、或更新公开技能列表时使用。
  也适用于用户说「更新 skills 文档」「同步技能」「注册技能到 claude」「刷新技能列表」。
---

# 更新 Skills 文档与 Claude Code 同步

你是 qi_Skills 项目的技能注册表管理员。当用户执行 `/update-skills-docs` 时，完成以下三件事：

1. **维护注册表** — 扫描 `skills/` 下所有技能（含嵌套目录），更新 `skills-registry.yaml`
2. **更新 README** — 根据注册表中 `sync: true` 的条目更新公开技能列表
3. **同步到 Claude Code** — 将 `sync: true` 的技能软链接到 `~/.claude/skills/`

## 快速执行

优先运行仓库脚本（推荐）：

```bash
cd <repo-root>
python3 scripts/skills-registry.py all
```

子命令：
- `scan` — 仅扫描并更新 `skills-registry.yaml`
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

注意嵌套结构：技能可能位于 `skills/travel_journal/travel-journal/` 等子目录中，不要假设所有技能都在 `skills/` 的直接子目录。

### 2. 解析并更新 skills-registry.yaml

注册表路径：`skills-registry.yaml`（仓库根目录）

对每个发现的技能：
- 从 SKILL.md frontmatter 提取 `name` 和 `description`
- 根据目录位置推断 `category`（详见 [registry-format.md](./references/registry-format.md)）
- **保留已有的 `sync` 标记** — 这是唯一需要人工维护的字段
- 新发现的技能默认 `sync: false`

从注册表中移除已不存在的技能路径，并在摘要中报告。

### 3. 同步到 Claude Code

仅对 `sync: true` 的技能创建软链接：

```bash
ln -sfn <绝对路径/技能目录> ~/.claude/skills/<name>
```

规则：
- 链接名使用 frontmatter 的 `name`，不是目录名
- 如果 `~/.claude/skills/<name>` 已存在且指向其他位置，替换为新的链接
- 如果某技能从 `sync: true` 改为 `false`，移除指向本仓库的对应软链接
- 检测 `~/.claude/skills` 是否是指向本仓库的符号链接，若是则报错退出

`.claude/skills/` 下的私有 meta 技能（如本技能）不在此次同步范围内，除非用户明确要求。

### 4. 更新 README.md

找到 `## Skills 列表` 部分，**仅列出 `sync: true` 的技能**，按 category 分组：

```markdown
### Uncategorized

- **[idea-validator](./skills/idea-validator/SKILL.md)** — description
```

未同步的技能不出现在 README 中，但会保留在 `skills-registry.yaml` 中。

### 5. 输出变更摘要

报告：
- 注册表：总数 / 已同步数
- 新增、移除、元数据更新的技能
- 新链接 / 取消链接的技能
- 提醒用户：新技能需要手动将 `sync` 改为 `true` 才会同步

## Category 映射

| 目录模式 | Category |
|----------|----------|
| `skills/engineering/*` | Engineering |
| `skills/productivity/*` | Productivity |
| `skills/misc/*` | Misc |
| `skills/<group>/<skill>` | `<group>`（首段分组名，如 travel_journal） |
| `skills/<skill>` | Uncategorized |

## 注册表手动编辑

用户只需编辑 `sync` 字段：

```yaml
- path: skills/idea-validator
  name: idea-validator
  description: "..."
  category: uncategorized
  sync: true   # ← 改这里
```

完整格式说明见 [references/registry-format.md](./references/registry-format.md)。

## 注意事项

- 保持 README.md 的其他内容不变
- `description` 从 SKILL.md 自动同步，注册表中允许较长文本
- 不要修改用户未标记为 sync 的技能链接
- 运行前确认 `skills-registry.yaml` 中 sync 标记符合用户意图
