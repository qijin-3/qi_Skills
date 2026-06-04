---
name: update-skills-docs
description: 自动扫描 skills/ 目录，解析所有 SKILL.md 的 frontmatter，并更新 README.md 中的 skills 列表。当你在项目中增删改 skills 后使用。
---

# 更新 Skills 文档

你是一个负责自动更新 qi_Skills 项目文档的助手。当用户执行 `/update-skills-docs` 时：

## 执行步骤

1. **扫描 skills/ 目录**
   - 找到所有包含 `SKILL.md` 的目录
   - 排除 `deprecated/` 目录

2. **解析每个 SKILL.md**
   - 提取 YAML frontmatter 中的 `name` 和 `description`
   - 根据 skill 的目录位置确定其 category（engineering, productivity, misc 等）

3. **更新 README.md**
   - 找到 `## Skills 列表` 部分
   - 按 category 分组更新 skills 列表
   - 格式：`- **[name](./skills/category/name/SKILL.md)** — description`

4. **输出变更摘要**
   - 报告新增、删除、更新的 skills
   - 显示更新后的 README.md 片段

## Category 映射

根据目录位置自动分类：
- `skills/engineering/*` → Engineering
- `skills/productivity/*` → Productivity
- `skills/misc/*` → Misc
- `skills/*` (直接子目录) → Uncategorized

## 注意事项

- 保持 README.md 的其他内容不变
- 使用 markdown 列表格式
- 确保 description 简洁清晰
