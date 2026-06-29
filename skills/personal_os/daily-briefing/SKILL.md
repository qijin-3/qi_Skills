---
name: daily-briefing
version: 1.1.0
description: >
  每日早报调度。用户说"发一下早报"、"早报"时触发；也由调度系统定时调用。
  读取当前目标与任务分组 → 偏差扫描 → 挑 ≤3 条今天要做 → 写评论 + 日志 + 每日快照。
  是每日调度的起点，为晚报和周复盘提供数据。
---

# Daily Briefing

读目标 + 分组任务 → 偏差扫描 → 选今天要做（≤3条）→ 写评论 → 写日志 → 保存快照 → 发消息。

## 开始前

1. 解析 `PERSONAL_OS_ROOT`：按顺序检查 `$PERSONAL_OS_ROOT` → `~/Personal_OS` → `~/SynologyDrive/Sync/OS/Personal_OS` → `~/SynologyDrive/SynologyDrive/Sync/OS/Personal_OS`，首个同时存在 `references/path-resolution.md` 与 `references/config.md` 的目录即为根目录
2. Read `{PERSONAL_OS_ROOT}/references/config.md`，取所有变量（FEISHU_BASE_TOKEN、TABLE_MONTHLY、TABLE_WEEKLY、TABLE_LOGS、MY_* 分组、USER_OPEN_ID、FIELD_IMPORTANCE）。

飞书 CLI 命令语法 → Read `references/lark-commands.md`（Step 3 移动任务前必读）。

今日日期：`YYYY-MM-DD`，本周：`Wnn`。

---

## 工作流

### Step 1：读取目标与任务

- **进行中目标**：读 `TABLE_MONTHLY`（状态=进行中，周期=本月）+ `TABLE_WEEKLY`（状态=进行中，周期=本周），提取月度目标和本周主线的标题/验收标准
- **各分组任务**：读 `MY_TODAY`、`MY_WEEK`、`MY_MONTH`、`MY_UNPLANNED`，记录每条任务的 guid、summary、importance、created_at

### Step 2：偏差扫描

遍历 MY_TODAY / MY_WEEK / MY_MONTH 中的任务：

- `created_at` > 本周周日 20:00（周定稿时间）→ 视为"周内新增"
- 同时满足以下任一 → 标记偏差并预警：
  - 重要性 = 高
  - 标题语义与本周/月目标明显冲突（如"开新项目"而月目标是"完成旧项目"）

预警消息示例：
```
⚠️ 发现周内新增高优任务：「{任务标题}」
→ 纳入本周还是放未安排？它会挤掉「{当前本周主线}」
```

### Step 2.5：任务分组调度（偏差扫描后执行）

Read `references/task-triage.md`，执行日视角的双向任务调度（自动完成，无需用户确认）。

---

### Step 3：挑选今天要做（≤3 条）

**优先级逻辑（按顺序）：**
1. MY_TODAY 已有任务 → 评估是否合适（≤3 条、高杠杆优先）
2. MY_TODAY 为空或 <1 条 → 从 MY_WEEK 补 1–2 条
3. MY_TODAY 超过 3 条 → 移动超出的到 MY_WEEK

**高杠杆判断**（优先选）：重要性=高 / 与本周目标直接关联 / 清单属于 Writing/Growing/Projects

**移到 MY_WATCH**（不适合今天）：重要性=低 且与目标无关 / Routine 类且今日已有其他 Routine

### Step 4：为今天要做的每条任务添加评论

评论内容说明"为什么今天做这条"（高杠杆/对齐目标/截止日等）。

命令见 `references/lark-commands.md`。

### Step 5：写日志表

查找今日日志记录：
- 不存在 → 创建，写入「日期」和「今日计划」（任务标题列表，换行分隔）
- 已存在 → 更新「今日计划」字段

### Step 6：保存每日快照

写入 `{PERSONAL_OS_ROOT}/state/daily_snapshot_{YYYY-MM-DD}.json`。

快照记录**晨间状态**（早报执行时刻），是晚报行为分析的基准线。`am.MY_TODAY` 需标记哪些是 AI 放入（`ai_placed: true`），以便晚报判断用户主动行为。

```json
{
  "date": "YYYY-MM-DD",
  "week": "YYYY-Wnn",
  "am": {
    "MY_TODAY": [
      {"guid": "...", "summary": "...", "ai_placed": true},
      {"guid": "...", "summary": "...", "ai_placed": false}
    ],
    "MY_WEEK":  [{"guid": "...", "summary": "..."}],
    "MY_MONTH": [{"guid": "...", "summary": "..."}],
    "MY_WATCH": [{"guid": "...", "summary": "..."}]
  },
  "behaviors": [],
  "patterns": []
}
```

`state/` 目录下超过 30 个快照时，删除最旧的。

---

## 注意事项

- MY_TODAY 上限 **3 条**，超出的移 MY_WEEK（不是 MY_WATCH）
- 不改任务标题、描述、重要性（只移分组 + 加评论）
- 快照文件是行为分析和周/月复盘的数据来源，**必须每天保存**
