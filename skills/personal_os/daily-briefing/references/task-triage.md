# Daily Briefing · 任务分组调度（日视角）

> **本文件是 daily-briefing 技能的专属参考文件，位于 `daily-briefing/references/` 目录下，不在 `PERSONAL_OS_ROOT/references/` 中。**
>
> 在偏差扫描后、挑选今天要做之前执行。
> 调度完成后直接告知结果，**不需要用户确认**。
>
> 执行前确保已运行变量加载命令（见 `config.md`），使 `$MY_TODAY`、`$MY_WEEK` 等变量可用。

## 分组定义

| 分组 | 含义 |
|------|------|
| MY_TODAY | 今天实际要做的，≤3 条 |
| MY_WEEK | 本周要做但今天不做的 |
| MY_MONTH | 本周不做、月内仍需推进的 |
| MY_UNPLANNED | 积压待处理（日调度不操作此分组） |
| MY_WATCH | **你认为重要，但 AI 判断今天不应安排的任务** |

## 保持关注的边界（硬规则）

**MY_WATCH 只能从以下三个分组移入：**
- MY_TODAY
- MY_WEEK
- MY_MONTH

**日调度不操作 MY_UNPLANNED，也不从 MY_UNPLANNED 移入 MY_WATCH。**

## 读取分组

仅读取 MY_TODAY、MY_WEEK、MY_MONTH（必要时参考 MY_WATCH 是否有误放任务）。

```bash
# 使用已加载的环境变量
lark-cli task sections tasks --as user \
  --section-guid "$MY_TODAY" \
  --format json --page-all
```

## 判断逻辑

**第一步：清理 MY_TODAY 中不适合今天的任务**

| 当前分组 | 判断 | 目标分组 |
|---------|------|---------|
| MY_TODAY | 与本周主线无关，仍属月目标 | → MY_WEEK |
| MY_TODAY | 你认为重要，但与本周/月目标都无关 | → MY_WATCH |
| MY_TODAY | 已是今天应做 | 保留 |

**第二步：从 MY_WEEK 补充今天的任务**（仅当 MY_TODAY < 3 条时）

从 MY_WEEK 中选出最适合今天的任务补入 MY_TODAY，优先级：
1. 与本周主线最直接相关
2. 重要性=高
3. 截止日期最近

每次从 MY_WEEK 移入后，MY_TODAY 总数不超过 3 条。

**第三步：检查 MY_TODAY 是否超过 3 条**

若超过 3 条，将优先级最低的移回 MY_WEEK（不移入 WATCH）。

**移入 MY_WATCH 时必须在输出中说明**：「你认为重要，但今天不应安排，原因是……」

## 执行移动

```bash
# 替换 $MY_WEEK 为目标分组变量（$MY_TODAY / $MY_WEEK / $MY_MONTH / $MY_WATCH）
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<task_guid>" \
  --section-guid "$MY_WEEK"
```


## 输出结果

```
📋 今日任务已编排

今天要做（{N}/3 条）：
  1. 「{任务名}」（{高杠杆/对齐主线/截止日等}）

移出「今天要做」：{N} 条
  - 「{任务名}」→ 本周计划
  - 「{任务名}」→ 保持关注（你认为重要，但今天不应安排：{原因}）
```
