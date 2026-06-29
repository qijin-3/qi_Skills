---
name: quick-task
version: 3.2.0
description: >
  飞书任务捕获入口。用户说"帮我记一下"、"我想做X"、"有个任务"、"待办"、"记得X"、
  "以后要做Y"、"想法"等时，立即使用本技能，不要犹豫。
  从一句话自动选清单（Idea/Writing/Growing/Projects/Routine）、设重要性、落入「未安排」。
  即使用户没有明确说「建任务」，只要消息里包含可执行事项或待办意图，就触发本技能。
  与 diary-capture 互斥：有行动意图 → quick-task；纯感受/见闻 → diary-capture。
---

# Quick Task

用户说一句话 → 识别任务 → 选清单 → 创建飞书 Task → 简短回复。

## 开始前

Read `Personal-os/references/config.md`，取 `USER_OPEN_ID`、`MY_UNPLANNED` 及清单 GUID。

## 工作流

```
1. 识别任务（标题 / 描述 / 截止日期）  → Read references/task-extraction.md
2. 选清单                              → Read references/list-rules.md
3. 调用 API 创建                       → Read references/api.md
4. 回复用户                            → Read references/reply-format.md
```

- **1–2 条**：直接创建
- **≥3 条**：列出清单，用户确认后批量创建

## 本技能的边界

只做一件事：**把用户的任务写进飞书 Task**。

创建后不改标题/描述，不移动分组（新任务始终落入 `MY_UNPLANNED`），回复保持简短，不追加分析或建议。
