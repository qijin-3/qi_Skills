---
name: weekly-review
version: 1.2.0
description: >
  周复盘。用户说"做一下周复盘"、"本周总结"、"复盘"时触发；周日晚由调度系统调用。
  收集上周客观数据 → 动量检测 → 上周目标打分 → 行为信号分析 → 写入 weekly-review.md
  → 同步归档上周 TABLE_WEEKLY（完成度/状态/总结）。
  是 weekly-plan 的前置步骤，产出评分和行为信号作为下周规划输入。
---

# Weekly Review

上周数据 → 动量检测 → 打分 → 行为信号分析 → 写入 weekly-review.md → **同步 Base 周目标表**。

---

> **【文件路径说明】**
> - **技能参考文件**（`[技能参考]`）：与本 SKILL.md **同级**的 `references/` 目录，路径为 `weekly-review/references/xxx.md`。包括 `lark-commands.md`、`weekly-review-template.md`。
> - **Personal OS 数据文件**：`{PERSONAL_OS_ROOT}/content/` 或 `{PERSONAL_OS_ROOT}/state/` 下。

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
- Read `{PERSONAL_OS_ROOT}/content/north-star.md`，取三个战略支柱名称
- Read `{PERSONAL_OS_ROOT}/content/about-me.md`（仅「工作风格与偏好」「时间管理」两节）

**Step 0d：读飞书 CLI 命令语法**
Read `[技能参考]/lark-commands.md`（Step 1 数据拉取前必读）。

计算周期：
- 上周：`{YYYY}-W{nn-1}`（上周一 00:00 ~ 上周日 23:59，UTC+8）
- 本周：`{YYYY}-W{nn}`
- 本月：`{YYYY}-{MM}`

---

## 工作流概览

| Step | 动作 | 能否跳过 |
|------|------|--------|
| 1 | 收集上周客观数据 | 不可跳过 |
| 2 | 发上周复盘摘要 | 不可跳过 |
| 2.5 | 动量检测 | **不可跳过，即使用户催促** |
| 3 | 等待用户回应 | 可选 |
| 4 | 上周目标打分（仅提议，不写 Base） | 不可跳过 |
| 5 | 行为信号分析 | 无快照数据时可跳过 |
| 6 | 写入 weekly-review.md | 不可跳过 |
| 7 | 同步上周周目标到 Base | **不可跳过**（Step 1d 为 0 条时除外） |

---

### Step 1：收集上周客观数据

| 子步 | 数据源 | 提取内容 |
|------|--------|---------|
| 1a | 飞书任务（只用「我负责的」接口）| 上周完成总数 + 清单分布 |
| 1b | `$TABLE_LOGS` 上周记录 | `今日任务完成度` 均值、`主线推进情况` 天数 |
| 1c | north-star.md × 1a 清单分布 | 各支柱推进状态（推进/未推进） |
| 1d | `$TABLE_WEEKLY`（周期=上周） | 上周所有周目标记录 |
| 1e | `state/daily_snapshot_{date}.json`（上周每日） | `behaviors` + `patterns` 全量汇总（供 Step 5 用）|

> **禁止**：`lark-cli task +search`（易超时）；只用 `+get-my-tasks` / `sections tasks`。

---

### Step 2：发上周复盘摘要

```
📊 上周（{YYYY}-W{nn-1}，{MM-DD}~{MM-DD}）复盘

✅ 完成 {N} 条：Writing:{n} | Growing:{n} | Projects:{n} | Routine:{n}
📋 平均完成率：{X}%，主线推进 {n}/7 天
🌟 北极星：内容杠杆:{状态} | 产品杠杆:{状态} | 能力复利:{状态}
🔄 分组博弈：{快照摘要，无数据则写「无快照数据」}

你觉得上周最值得保留 / 最该改的一件事是什么？（可跳过）
```

---

### Step 2.5：动量检测（不可跳过，即使用户说「直接到下周吧」）

读 `$TABLE_MONTHLY` 本月进行中目标，对比 `$TABLE_LOGS` 最近 2 周 `主线推进情况`：

```
⚠️ 动量预警：本月目标「{目标}」已连续 {N} 天没有推进。
下周 weekly-plan 建议优先指向这里。
```

无预警时告知"本月所有目标都有推进"即可，不输出警告。

---

### Step 3：等待用户回应（可选）

等用户输入感受，或直接说"继续"/"跳过"。记录用户回应用于 weekly-review.md「偏离与原因」节。

---

### Step 4：上周目标打分（提议分数，Step 7 再写 Base）

对 Step 1d 每条 TABLE_WEEKLY 记录逐条提议分数（0–1 小数）：

```
📝 「{周目标主线}」打分建议：{X}%
依据：{完成任务数 × 验收标准对比，1-2 句}
确认？（或输入你的分数）
```

记录每条目标的最终分数（用户确认值，或 30 分钟内无回应则用建议分数并在输出注明「可异议」）。

**本步只收集分数，不写 Base**。完成度、状态、`总结` 在 Step 7 统一 upsert。

打分规则（Step 7 写入时沿用）：
- `完成度`：分数 ÷ 100（0–1 小数）
- `状态`：≥0.8 → 已达成；<0.8 → 已调整

---

### Step 5：行为信号分析

读取上周每日快照（`{PERSONAL_OS_ROOT}/state/daily_snapshot_{YYYY-MM-DD}.json`，上周一到上周日共 7 个），汇总 `behaviors` 和 `patterns`，按任务聚合：

| 信号类型 | 判断条件 | 含义 |
|---------|---------|------|
| 🔴 回避 | 某任务 `user_removed` ≥2 次，或 `stale` ≥3 天 | 你对这个任务有抗拒感 |
| 🟢 自驱 | 某任务有 `user_added` 且当日 completed | 你真正想做的事 |
| 📊 AI 配合率 | `completed_ai` / (`completed_ai` + `user_removed`) | 你对 AI 安排的接受程度 |

将行为信号追加到 `{PERSONAL_OS_ROOT}/content/{YYYY}/{MM}/about-me-updates.md` 末尾。

若上周无快照数据 → 跳过，注明"无快照数据"。

---

### Step 6：写入 weekly-review.md（不可跳过）

路径：`{PERSONAL_OS_ROOT}/content/{YYYY}/{MM}/weekly-review.md`（不存在则先创建）

模板 → Read `[技能参考]/weekly-review-template.md`（**注意：此文件在技能 references/ 目录，不在 PERSONAL_OS_ROOT/references/ 下**）

在文件标题后**插入**新节（最新周在最上方），包含 Steps 1–5 所有数据。

---

### Step 7：同步上周周目标到 Base（必须执行）

对 Step 1d 查到的**每一条**上周 `$TABLE_WEEKLY` 记录，用其 `record_id` 执行 upsert（命令见 `[技能参考]/lark-commands.md`）。

| 字段 | 值 |
|------|-----|
| 完成度 | Step 4 最终分数 ÷ 100（0–1 小数） |
| 状态 | ≥0.8 → 已达成；<0.8 → 已调整 |
| 总结 | 该条「主线」的周复盘小结（见下） |

**`总结` 写法**（每条主线单独写，≤150 字）：
1. 本周该主线的完成情况（对照验收标准，1 句）
2. 关键偏离或收获（来自 Step 3 用户回应 / Step 5 行为信号，有则写）
3. 下周改进点（来自「可提升点」，有则写 1 句）

同周若仅 1 条周目标，可写入更完整的周级总结；多条时各写各自主线相关部分。

**硬规则**：
- **必须**使用 Step 1d 返回的 `record_id`，**禁止**不带 `record_id` 的 upsert（避免误建重复记录）
- 同周 N 条记录须**逐条**更新，不得漏更新
- Step 1d 返回 0 条 → 跳过本步，输出注明「上周无周目标记录」
- 未完成 Step 7（且有可更新记录时）→ 周复盘视为**未完成**

完成后向用户确认：

```
✅ 已归档上周（{YYYY-W{nn-1}}）周目标 {N} 条：完成度 + 状态 + 总结已写入 Base
```

---

## 注意事项

- 任务读取只用「我负责的」接口，禁止 `+search`
- **动量检测不可跳过**，即使用户催促也必须过一遍
- **Step 7 Base 同步不可跳过**（有可归档的周目标时）；创建下周目标由 `weekly-plan` 负责，本技能只归档上周
- 月目标调整不在本技能处理，告知等到月初运行 `monthly-plan`
- 行为信号分析无数据时跳过，不报错
