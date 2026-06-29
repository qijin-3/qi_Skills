---
name: evening-review
version: 2.0.0
description: >
  每日晚报收尾。用户说"发一下晚报"、"晚报"时触发；调度系统定时调用。
  读取今日完成任务 → 完成率预警 → 处理未完成项 → 判断主线 → 拼装日记
  → 写日志（完成度/主线推进/日记路径）→ 快照 diff → 追加每日观察。
  写入日志表的数据是周复盘/月复盘的核心输入，必须每天执行。
---

# Evening Review

## 开始前

Read `Personal-os/references/config.md`，取：
- `FEISHU_BASE_TOKEN`、`TABLE_LOGS`、`TABLE_WEEKLY`
- `MY_TODAY`、`MY_WEEK`、`MY_WATCH`
- `FIELD_LOG_COMPLETION_RATE`、`FIELD_LOG_MAINLINE`、`FIELD_LOG_NOTE`、`FIELD_LOG_DIARY_PATH`
- `USER_OPEN_ID`、`PATH_DIARY`、`PATH_DIARY_PENDING`

今日日期：`YYYY-MM-DD`。

---

## 工作流

飞书 CLI 命令语法 → Read `references/lark-commands.md`（Step 4 处理未完成前必读）。

### Step 1：获取今日完成任务

按 `completed_at` 过滤今日（00:00–23:59 UTC+8）完成的任务，提取 guid、summary。

数据源只用 `completed_at` 时间戳，不以分组状态代替。

### Step 2：读今日计划 + 计算完成率

从 `TABLE_LOGS` 查今日记录，取「今日计划」字段（早报写入的任务标题列表）。

**完成率** = 今日完成中属于今日计划的条数 / 今日计划总数（0–1 小数）

### Step 3：连续低完成率检查

查 TABLE_LOGS 最近 2 天的 `今日任务完成度`（FIELD_LOG_COMPLETION_RATE）：

- 连续 ≥2 天 < 0.33 → 触发预警，然后继续执行（不阻塞）：

```
⚠️ 连续 2 天完成率低于 1/3

今日计划 {N} 条，完成 {M} 条。
是任务太多，还是方向有点不对？聊一聊？
```

### Step 4：处理未完成项

获取 MY_TODAY 中未完成任务（分组列表过滤掉已完成的）。

对每条未完成任务：
1. 添加评论："晚报 {YYYY-MM-DD}：今天未完成。原因待跟踪。"
2. 对比今日快照 vs 昨日快照：
   - 同一任务连续 ≥2 天在 MY_TODAY 且未完成 → 移到 MY_WEEK
   - 只未完成 1 天 → 留在 MY_TODAY（明天早报再判断）

命令见 `references/lark-commands.md`。

### Step 5：判断主线推进情况

读 TABLE_WEEKLY（周期=本周 `YYYY-Wnn`，状态=进行中），与今日完成任务关联判断：

| 判断 | 结果 |
|------|------|
| 有完成任务与周目标直接相关 | 推进 |
| 有周边任务但无直接关联 | 部分推进 |
| 无任何关联 | 未推进 |

记录一句依据（如"完成了 X，与本周目标 Y 直接相关"）。

### Step 6：拼装今日日记

Read `references/diary-assembly.md`，按其步骤执行日记拼装。

拼装完成后 diary-assembly 会更新 `TABLE_LOGS.日记路径` 并清空 pending。若拼装失败，继续晚报，在输出中注明"日记拼装失败，请手动检查"。

### Step 7：更新日志表

更新今日 TABLE_LOGS 记录（Record ID 来自 Step 2 查询）：

| 字段 | 值 |
|------|-----|
| 今日完成任务 | 完成任务标题（换行分隔） |
| 今日任务完成度 | 完成率 0–1 小数 |
| 主线推进情况 | 推进 / 部分推进 / 未推进 |
| 说明 | 主线依据一句话 |
| 日记路径 | Step 6 写入的路径（若失败留空） |

命令见 `references/lark-commands.md`。

### Step 8：行为分析 + 更新快照

读取今日快照（`state/daily_snapshot_{YYYY-MM-DD}.json`）的 `am` 字段，与当前飞书分组状态对比，识别用户的真实行为，写入 `behaviors` 和 `patterns`。

**行为识别规则：**

| 行为类型 | 判断条件 | pattern 标签 |
|---------|---------|-------------|
| `completed_ai` | 在 am.MY_TODAY 且 ai_placed=true，今日已完成 | `completed_ai:{guid}` |
| `completed_user` | 在 am.MY_TODAY 且 ai_placed=false，今日已完成 | `completed_user:{guid}` |
| `user_removed` | 在 am.MY_TODAY 且 ai_placed=true，晚间不在 MY_TODAY 且未完成（用户主动移出） | `user_removed:{guid}` |
| `user_added` | 晚间在 MY_TODAY，但不在 am.MY_TODAY（用户白天主动加入） | `user_added:{guid}` |
| `stale` | 今日和昨日快照 am.MY_TODAY 都有该任务，且今日未完成，连续 N 天 | `stale:{guid}:{N}` |

将识别结果写入今日快照：

```json
{
  "behaviors": [
    {"type": "user_removed", "guid": "...", "summary": "..."},
    {"type": "stale",        "guid": "...", "summary": "...", "days": 2},
    {"type": "completed_ai", "guid": "...", "summary": "..."}
  ],
  "patterns": [
    "user_removed:guid1",
    "stale:guid2:2",
    "completed_ai:guid3"
  ]
}
```

这些 patterns 会被周复盘/月复盘读取，用于分析抗拒感、偏好和自驱行为。

### Step 9：追加每日观察到 about-me-updates.md

路径：`Personal-os/content/{YYYY}/{MM}/about-me-updates.md`

若不存在 → 先创建，首行为 `# {YYYY}-{MM} 关于我 · 更新记录`。

在文件末尾追加（只记录客观信号，不做解读）：

```markdown
### {YYYY-MM-DD} 每日观察

- 完成率：{M}/{N}（{X}%）
- 主线推进：{推进 / 部分推进 / 未推进}
{若有 stale} - 滞留任务：「{任务名}」连续 {n} 天未完成
{若有 user_removed} - 被移出：「{任务名}」（早报放入，用户自行移出）
{若有 user_added} - 自加：「{任务名}」（用户主动加入今天）
{若今日 diary.md 有内容} - 日记信号：{从今日日记节提取 1-2 个状态关键词，原词不改写}
```

只记录有信号的条目；无 stale/被移出/日记的平淡天，只写前两行。

Step 9 失败不阻塞晚报，在输出中注明即可。

---

## 边界说明

- 完成任务数据源只用 `completed_at`，不读分组状态
- 未完成任务评论不追问原因（只记录），避免打扰
- 日记拼装逻辑见 `references/diary-assembly.md`
