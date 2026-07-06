---
name: evening-review
version: 2.2.0
description: >
  每日晚报收尾。用户说"发一下晚报"、"晚报"时触发；调度系统定时调用。
  读取今日完成任务 → 完成率预警 → 处理未完成项 → 判断主线 → 拼装日记
  → 统一写入日志表（今日计划 + 完成度/主线推进）→ 快照 diff → 追加每日观察。
  日志表每天仅由本技能写入一条记录，是周复盘/月复盘的核心输入，必须每天执行。
---

# Evening Review

## 【文件路径说明】

> - **技能参考文件**（`[技能参考]`）：与本 SKILL.md **同级**的 `references/` 目录下，路径为 `evening-review/references/xxx.md`。包括 `lark-commands.md`、`diary-assembly.md`。
> - **Personal OS 数据文件**：`{PERSONAL_OS_ROOT}/content/` 或 `{PERSONAL_OS_ROOT}/state/` 下。
> - **绝对不能混淆**：`diary-assembly.md` 是技能参考文件，**不在** `{PERSONAL_OS_ROOT}/references/` 中。

---

## 开始前（必须全部完成，不可跳过）

**Step 0a：解析根目录**
按顺序检查，首个同时存在 `references/path-resolution.md` 与 `references/system.json` 的目录即为 `PERSONAL_OS_ROOT`：
1. 环境变量 `$PERSONAL_OS_ROOT`
2. `~/Personal_OS`
3. `~/SynologyDrive/Sync/OS/Personal_OS`
4. `~/SynologyDrive/SynologyDrive/Sync/OS/Personal_OS`

**Step 0b：加载系统变量**（必须执行，后续所有飞书命令依赖此步）
Read `{PERSONAL_OS_ROOT}/references/config.md`，找到「调什么命令（加载系统变量）」部分，执行 `eval "$(python3 ...)"` 命令。

今日日期：`YYYY-MM-DD`。

---

## 工作流

飞书 CLI 命令语法 → Read `[技能参考]/lark-commands.md`（Step 4 处理未完成前必读）。

### Step 1：获取今日完成任务

按 `completed_at` 过滤今日（00:00–23:59 UTC+8）完成的任务，提取 guid、summary。

数据源只用 `completed_at` 时间戳，不以分组状态代替。

### Step 2：读今日计划 + 计算完成率

从今日快照读取晨间计划（**不查日志表**）：

路径：`{PERSONAL_OS_ROOT}/state/daily_snapshot_{YYYY-MM-DD}.json` → `am.MY_TODAY[].summary`（换行拼接即为「今日计划」）

| 快照情况 | 处理 |
|---------|------|
| 存在 | 用 `am.MY_TODAY` 的 summary 列表作为今日计划 |
| 不存在（早报未运行） | 今日计划为空；完成率记为 0，Step 7 写入日志时 `今日计划` 留空并在输出注明 |

**完成率** = 今日完成中属于今日计划的条数 / 今日计划总数（0–1 小数；计划数为 0 时完成率为 0）

### Step 3：连续低完成率检查

查 TABLE_LOGS 最近 2 天的 `今日任务完成度`：

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

命令见 `[技能参考]/lark-commands.md`。

### Step 5：判断主线推进情况

读 `$TABLE_WEEKLY`（周期=本周 `YYYY-Wnn`，状态=进行中），与今日完成任务关联判断：

| 判断 | 结果 |
|------|------|
| 有完成任务与周目标直接相关 | 推进 |
| 有周边任务但无直接关联 | 部分推进 |
| 无任何关联 | 未推进 |

记录一句依据（如"完成了 X，与本周目标 Y 直接相关"）。

### Step 6：拼装今日日记

Read `[技能参考]/diary-assembly.md`（**注意：此文件在技能 references/ 目录，不在 PERSONAL_OS_ROOT/references/ 下**），按其步骤执行日记拼装。

拼装完成后 diary-assembly 会清空 pending。若拼装失败，继续晚报，在输出中注明"日记拼装失败，请手动检查"。

### Step 7：写入日志表（唯一写入方）

**`$TABLE_LOGS` 仅由晚报写入**。每天只允许一条记录；先查后写，禁止盲目新建。

用下方查询复用 `record_id`：

| 情况 | 动作 |
|------|------|
| 0 条 | 创建当日唯一记录（日期 + 今日计划 + 晚报字段，一次 upsert） |
| 1 条 | 带 `record_id` 全量更新（含今日计划），禁止不带 `record_id` 的 upsert |
| 多条 | 选有完整字段最多的一条更新，警告用户合并历史重复记录 |

写入字段：

| 字段 | 值 |
|------|-----|
| 日期 | 今日（仅创建时写入） |
| 今日计划 | Step 2 从快照得到的任务标题（换行分隔） |
| 今日完成任务 | 完成任务标题（换行分隔） |
| 今日任务完成度 | 完成率 0–1 小数 |
| 主线推进情况 | 推进 / 部分推进 / 未推进 |
| 说明 | 主线依据一句话 |

命令见 `[技能参考]/lark-commands.md`。

### Step 8：行为分析 + 更新快照

读取今日快照（`{PERSONAL_OS_ROOT}/state/daily_snapshot_{YYYY-MM-DD}.json`）的 `am` 字段，与当前飞书分组状态对比，识别用户的真实行为，写入 `behaviors` 和 `patterns`。

**行为识别规则：**

| 行为类型 | 判断条件 | pattern 标签 |
|---------|---------|-------------|
| `completed_ai` | 在 am.MY_TODAY 且 ai_placed=true，今日已完成 | `completed_ai:{guid}` |
| `completed_user` | 在 am.MY_TODAY 且 ai_placed=false，今日已完成 | `completed_user:{guid}` |
| `user_removed` | 在 am.MY_TODAY 且 ai_placed=true，晚间不在 MY_TODAY 且未完成（用户主动移出） | `user_removed:{guid}` |
| `user_added` | 晚间在 MY_TODAY，但不在 am.MY_TODAY（用户白天主动加入） | `user_added:{guid}` |
| `stale` | 今日和昨日快照 am.MY_TODAY 都有该任务，且今日未完成，连续 N 天 | `stale:{guid}:{N}` |

将识别结果写入今日快照的 `behaviors` 和 `patterns` 字段。

### Step 9：追加每日观察到 about-me-updates.md

路径：`{PERSONAL_OS_ROOT}/content/{YYYY}/{MM}/about-me-updates.md`

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
- 今日计划只从本地快照读取，不依赖日志表回读
- 日志表由晚报独占写入，早报不得操作 `$TABLE_LOGS`
- 未完成任务评论不追问原因（只记录），避免打扰
- 日记拼装逻辑见 `[技能参考]/diary-assembly.md`
