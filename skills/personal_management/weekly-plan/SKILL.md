---
name: weekly-plan
version: 1.0.0
description: >
  下周计划安排。用户说"安排下周"、"做下周计划"、"周计划"时触发；通常在 weekly-review 完成后运行。
  时间核验 → 任务分组调度 → 提议各月度目标本周主线 → 写入 TABLE_WEEKLY + weekly-review.md 计划节。
  建议先运行 weekly-review 获得上周评分和行为信号，再运行本技能安排下周。
---

# Weekly Plan

时间核验 → 任务分组调度 → 提议下周各目标主线 → 写入 TABLE_WEEKLY。

## 开始前

1. Read `Personal-os/references/config.md`，取所有变量
2. Read `Personal-os/content/north-star.md`，取三支柱名称
3. Read `Personal-os/content/about-me.md`（仅「工作风格与偏好」「时间管理」两节，用于负荷判断）
4. 可选：读取本月 `weekly-review.md` 最新节，获取上周行为信号和动量预警输入

计算：本周 `{YYYY}-W{nn}`，本月 `{YYYY}-{MM}`。

飞书 CLI 命令 → Read `references/lark-commands.md`。

---

## 工作流概览

| Step | 动作 | 详情 |
|------|------|------|
| 1 | 时间核验 | 本文 §Step 1（不可跳过） |
| 2 | 任务分组调度 | `references/task-triage.md` |
| 3 | 提议下周各目标主线 | 本文 §Step 3 |
| 4 | 确认并写入 | 本文 §Step 4 + `references/lark-commands.md` |

---

### Step 1：时间核验（不可跳过）

```
下周有没有特殊安排？（出行、会议密集、其他事情）
```

等用户回答。若有特殊安排 → Step 3 主线适当缩量，或给出"至少完成 X"的最低标准。

---

### Step 2：任务分组调度（自动执行，无需确认）

Read `references/task-triage.md`，执行周视角双向任务调度：

- 拉取 MY_TODAY / MY_WEEK / MY_MONTH / MY_UNPLANNED / MY_WATCH 各分组
- 基于本周主线方向移动任务
- MY_WEEK ≤8 条；MY_TODAY ≤5 条
- 输出调度摘要（移入/移出条数），进入 Step 3

> MY_WATCH 只能从 MY_TODAY / MY_WEEK / MY_MONTH 移入，**不能**从 MY_UNPLANNED 移入。

---

### Step 3：提议下周各目标主线

读 TABLE_MONTHLY 本月所有进行中目标，结合 weekly-review 行为信号和动量预警，逐条提议本周具体行动（1 句话）。

优先顺序：
1. weekly-review 动量预警的目标（最高优先）
2. 北极星支柱上周未推进对应目标
3. 本月完成度最低的目标

```
🚀 下周各目标主线建议：

| 月度目标 | 本周推进内容 | 领域 |
|---------|------------|------|
| {月目标1} | {一句话具体行动} | {领域} |
| {月目标2} | {一句话具体行动} | {领域} |

{若有行为信号输入 → ⚠️ 注意：「{任务}」上周已连续移出/停滞，本周降低优先级或直接移出计划}
{若有时间限制 → 考虑{特殊安排}，建议最低完成：{最小可行标准}}
{若某月目标本周无行动 → 「{目标名}」：本周暂无行动，不建记录}

确认，还是你有其他想法？
```

---

### Step 4：确认并写入

用户确认后：

**4a. TABLE_WEEKLY 写入**（命令见 `references/lark-commands.md`）
- 为每个本周有具体行动的月度目标，分别创建一条 TABLE_WEEKLY 记录
- 每条记录关联对应月度目标的 record_id
- 本周无行动的月度目标不建记录

**4b. 追加 weekly-review.md 计划节**（路径和模板见 `references/weekly-review-template.md`）

---

## 注意事项

- 时间核验不可跳过
- MY_WATCH 限制：只能从 MY_TODAY / MY_WEEK / MY_MONTH 移入
- 大方向（月目标）不在本技能调整；若用户提出 → 告知等到月初 `monthly-plan`
- 若本月 weekly-review.md 不存在，创建时检查 `content/{YYYY}/{MM}/` 目录是否存在
