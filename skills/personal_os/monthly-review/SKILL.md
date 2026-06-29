---
name: monthly-review
version: 1.0.0
description: >
  月度复盘。用户说"做月度复盘"、"上月总结"、"月底了"时触发；月末最后一天由调度系统调用。
  收集上月客观数据 → 上月目标打分 → 月度行为模式分析 → About Me 更新提案 → 写入 about-me-updates.md。
  负责 about-me.md 的全部更新（monthly-plan 不涉及 About Me）；产出评分和行为报告作为下月 monthly-plan 输入。
---

# Monthly Review

上月数据 → 上月目标打分 → 月度行为分析 → About Me 更新提案 → 写入 about-me-updates.md / about-me.md。

## 开始前

1. 解析 `PERSONAL_OS_ROOT`：按顺序检查 `$PERSONAL_OS_ROOT` → `~/Personal_OS` → `~/SynologyDrive/Sync/OS/Personal_OS` → `~/SynologyDrive/SynologyDrive/Sync/OS/Personal_OS`，首个同时存在 `references/path-resolution.md` 与 `references/config.md` 的目录即为根目录
2. Read `{PERSONAL_OS_ROOT}/references/config.md`，取所有变量
3. Read `{PERSONAL_OS_ROOT}/content/north-star.md`，取三个战略支柱名称 + 衡量标准
4. Read `{PERSONAL_OS_ROOT}/content/about-me.md`，重点关注：
   - 「需要注意的特点/缺陷」：已知的时间陷阱和行为模式（Step 4 行为分析比对 + Step 5 更新提案）
   - 「时间管理」：实际作息，用于评估完成率合理性

飞书 CLI 命令 → Read `references/lark-commands.md`（Step 1 数据拉取前必读）
About Me 更新门槛 → Read `references/about-me-update-rules.md`（Step 5 执行前必读）

计算：上月 `{YYYY}-{MM-1}`（跨年处理 12→1），本月 `{YYYY}-{MM}`。

---

## 工作流概览

| Step | 动作 | 详情 |
|------|------|------|
| 1 | 收集上月数据 | 本文 §Step 1 |
| 2 | 发上月总结 | `references/output-templates.md` §Step 2 |
| 3 | 上月目标打分 | 本文 §Step 3 + `references/lark-commands.md` |
| 4 | 月度行为分析 | 本文 §Step 4 |
| 5 | About Me 更新提案 | 本文 §Step 5 + `references/about-me-update-rules.md` |

---

### Step 1：收集上月数据

**飞书 CLI 语法约束** → 执行 1a–1c 前必读 `references/lark-commands.md`。

**1a. 上月完成任务** — 只用「我负责的」接口，禁止 `+search`。统计总数与清单分布（Writing/Growing/Projects/Routine/Idea）。

**1b. 今天要做完成率** — 读 TABLE_LOGS，提取上月每日 `今日任务完成度` 字段，计算均值；无数据时如实说明。

**1c. 上月目标** — 读 TABLE_MONTHLY（周期=上月）+ 本地 `content/{YYYY}/{MM-1}/monthly-plan.md`，对照验收标准准备打分素材。

**1d. 月度行为数据** — 读上月所有 `state/daily_snapshot_{date}.json`，汇总所有 `behaviors` 和 `patterns`（供 Step 4 用）。无文件则跳过，Step 4 中注明"无快照数据"。

**1e. 北极星支柱推进** — 从 1a 清单分布对照 north-star.md 三支柱，识别哪个支柱推进了、哪个被忽略（月报必须呈现）。

**1f. 日记能量（可选）** — 若上月 `diary.md` 存在，扫描状态关键词，概述 ≤2 句。

---

### Step 2：发上月总结

按 `references/output-templates.md` · Step 2 模板输出，填入 Step 1 数据。

---

### Step 3：上月目标打分

对每条上月 TABLE_MONTHLY 记录逐条提议分数（0–1 小数）：

```
📝 「{目标标题}」打分建议：{X}%
依据：{完成情况 + 验收标准对比，1-2 句}
确认？（或输入你的分数）
```

用户确认后更新 TABLE_MONTHLY（命令见 `references/lark-commands.md`）：
- `目标完成度`：分数 ÷ 100
- `状态`：≥0.8 → 已达成；<0.8 → 已调整

---

### Step 4：月度行为分析

> 这是本技能的核心新增。从上月所有 daily_snapshot 中提炼行为模式，为下月 `monthly-plan` 制定策略提供数据输入，也作为 `about-me-updates.md` 的月度记录。

汇总 Step 1d 的 patterns，按任务 guid 聚合，计算：

| 分析维度 | 计算方式 | 输出含义 |
|---------|---------|---------|
| 月度回避清单 | `user_removed` 次数最多的 Top 3 任务 | 你一直在回避的任务 |
| 长期停滞任务 | `stale` 最大 days 值 Top 3 | 在今天要做里躺最久的任务 |
| 自驱偏好清单 | `user_added` 且 completed 次数最多的 Top 3 | 你真正主动想做的事 |
| AI 配合率 | `completed_ai` / (`completed_ai` + `user_removed`) | 你对 AI 安排的接受程度（月度） |
| 自主完成比例 | `completed_user` / 全部 completed | 脱离 AI 安排主动完成的比例 |

**将月度行为分析追加到上月 `content/{YYYY}/{MM-1}/about-me-updates.md` 末尾**：

```markdown
### {YYYY-MM} 月度行为总结

**月度回避：**
- 「{任务摘要}」被移出 {N} 次（你认为重要，但持续回避）
- 「{任务摘要}」停滞 {N} 天（一直在今天要做里但未推进）

**自驱偏好：**
- 「{任务摘要}」{N} 次主动加入 → 已完成（真实意愿）

**整月配合指数：**
- AI 安排完成率：{X}%（completed_ai / AI 安排总量）
- 自主完成比例：{Y}%（自发完成 / 总完成）
- 💡 模式解读：{1 句客观描述，如"你对 AI 安排的接受度较高，但遇到项目类任务有明显回避倾向"}
```

若无快照数据 → 写「本月无行为快照数据，{YYYY-MM+1} 起开始积累」，然后跳过。

**月度行为分析报告**同步输出给用户（简化版）：

```
📊 {YYYY-MM} 行为模式月报

🔴 回避信号 Top 3：
  1. 「{任务}」— 被移出 {N} 次 / 停滞 {N} 天
  ...

🟢 自驱信号 Top 3：
  1. 「{任务}」— {N} 次主动加入并完成
  ...

📊 配合指数：AI安排完成 {X}% / 自主完成 {Y}%

💡 下月 monthly-plan 参考：{1-2 句策略建议，如"可减少项目类任务数量，或改拆成更小粒度"}
```

---

### Step 5：About Me 更新提案

Read `references/about-me-update-rules.md` 了解各章节更新门槛，再执行。

读取上月 `content/{YYYY}/{MM-1}/about-me-updates.md`（包含每日观察节 + Step 4 写入的月度行为总结），对照 `about-me.md` 各章节，识别满足更新门槛的稳定模式。

将提案展示给用户（无满足门槛的模式则告知"本月无需更新 About Me"）：

```
📝 About Me 更新提案（基于上月每日观察 + 行为总结）

【{章节名}】
发现：{模式描述}（出现 {n} 次，{日期证据}）
改前：{原文}
改后：{新内容}
---
需要写入 about-me.md 吗？
```

**用户确认后，执行三步：**

① 精确修改 `{PERSONAL_OS_ROOT}/content/about-me.md`（只改本次相关段落，不改其他内容，不加 AI 风格语言）

② 在上月 `about-me-updates.md` 末尾追加确认记录：

```markdown
### {YYYY-MM-DD} 月度归纳确认

**更新章节**：{章节名}
**模式依据**：{模式描述，出现次数}
**修改摘要**：{改了什么，一句话}
```

③ 同步到飞书 Wiki（命令见 `references/lark-commands.md`）。Wiki 同步失败不影响本地文件，输出中注明即可。

**用户说"不用"** → 跳过，不改任何文件。
**上月 about-me-updates.md 不存在或无有效条目** → 跳过本步骤，不报错。

---

## 注意事项

- 任务读取只用「我负责的」接口，**禁止 `lark-cli task +search`**
- 无快照数据时跳过 Step 4，不报错
- `about-me.md` 的**全部更新责任**在本技能，monthly-plan 不做任何 about-me 修改
- 打分超时处理：30 分钟无回应 → 按建议分数写入，注明"可异议"
