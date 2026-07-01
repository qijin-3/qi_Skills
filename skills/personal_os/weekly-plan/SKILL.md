---
name: weekly-plan
version: 1.1.0
description: >
  下周计划安排。用户说"安排下周"、"做下周计划"、"周计划"时触发；通常在 weekly-review 完成后运行。
  时间核验 → 任务分组调度 → 提议各月度目标本周主线 → 写入 TABLE_WEEKLY + weekly-review.md 计划节。
  建议先运行 weekly-review 获得上周评分和行为信号，再运行本技能安排下周。
---

# Weekly Plan

时间核验 → 任务分组调度 → 提议下周各目标主线 → 写入 TABLE_WEEKLY。

---

> **【文件路径说明】**
> - **技能参考文件**（`[技能参考]`）：与本 SKILL.md **同级**的 `references/` 目录，路径为 `weekly-plan/references/xxx.md`。包括 `task-triage.md`、`lark-commands.md`、`weekly-review-template.md`。
> - **Personal OS 数据文件**：`{PERSONAL_OS_ROOT}/content/` 下。
> - **绝对不能混淆**：`task-triage.md` 是技能参考文件，**不在** `{PERSONAL_OS_ROOT}/references/` 中。

---

## 开始前（必须全部完成，不可跳过）

**Step 0a：解析根目录**
按顺序检查，首个同时存在 `references/path-resolution.md` 与 `references/system.json` 的目录即为 `PERSONAL_OS_ROOT`：
1. 环境变量 `$PERSONAL_OS_ROOT`
2. `~/Personal_OS`
3. `~/SynologyDrive/Sync/OS/Personal_OS`
4. `~/SynologyDrive/SynologyDrive/Sync/OS/Personal_OS`

**Step 0b：加载系统变量**（必须执行）
Read `{PERSONAL_OS_ROOT}/references/config.md`，找到「调什么命令（加载系统变量）」部分，执行 `eval "$(python3 ...)"` 命令。

**Step 0c：读基础文件**
- Read `{PERSONAL_OS_ROOT}/content/north-star.md`，取三支柱名称
- Read `{PERSONAL_OS_ROOT}/content/about-me.md`（仅「工作风格与偏好」「时间管理」两节，用于负荷判断）
- 可选：读取本月 `{PERSONAL_OS_ROOT}/content/{YYYY}/{MM}/weekly-review.md` 最新节，获取上周行为信号和动量预警输入

**Step 0d：读飞书 CLI 命令语法**
Read `[技能参考]/lark-commands.md`。

计算：本周 `{YYYY}-W{nn}`，本月 `{YYYY}-{MM}`。

---

## 工作流概览

| Step | 动作 | 能否跳过 |
|------|------|--------|
| 1 | 时间核验 | **不可跳过** |
| 2 | 任务分组调度 | 不可跳过（自动执行） |
| 3 | 提议下周各目标主线 | 不可跳过 |
| 4 | 确认并写入 | 不可跳过 |

---

### Step 1：时间核验（不可跳过）

```
下周有没有特殊安排？（出行、会议密集、其他事情）
```

等用户回答。若有特殊安排 → Step 3 主线适当缩量，或给出"至少完成 X"的最低标准。

---

### Step 2：任务分组调度（自动执行，无需用户确认）

Read `[技能参考]/task-triage.md`（**注意：此文件在技能 references/ 目录，不在 PERSONAL_OS_ROOT/references/ 下**），执行周视角双向任务调度：

- 拉取 MY_TODAY / MY_WEEK / MY_MONTH / MY_UNPLANNED / MY_WATCH 各分组
- 基于本周主线方向移动任务
- MY_WEEK ≤8 条；MY_TODAY ≤5 条
- 输出调度摘要（移入/移出条数），进入 Step 3

> MY_WATCH 只能从 MY_TODAY / MY_WEEK / MY_MONTH 移入，**不能**从 MY_UNPLANNED 移入。

---

### Step 3：提议下周各目标主线

读 `$TABLE_MONTHLY` 本月所有进行中目标，结合 weekly-review 行为信号和动量预警，逐条提议本周具体行动（1 句话）。

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

**4a. TABLE_WEEKLY 写入**（命令见 `[技能参考]/lark-commands.md`）
- 为每个本周有具体行动的月度目标，分别创建一条 TABLE_WEEKLY 记录
- 每条记录关联对应月度目标的 record_id
- 本周无行动的月度目标不建记录

**4b. 追加 weekly-review.md 计划节**（路径和模板见 `[技能参考]/weekly-review-template.md`）

---

## 注意事项

- **时间核验不可跳过**
- MY_WATCH 限制：只能从 MY_TODAY / MY_WEEK / MY_MONTH 移入
- 大方向（月目标）不在本技能调整；若用户提出 → 告知等到月初 `monthly-plan`
- 若本月 weekly-review.md 不存在，创建时检查 `content/{YYYY}/{MM}/` 目录是否存在
