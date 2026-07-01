# Weekly Plan · 任务分组调度（周视角）

> **本文件是 weekly-plan 技能的专属参考文件，位于 `weekly-plan/references/` 目录下，不在 `PERSONAL_OS_ROOT/references/` 中。**
>
> 在下周主线确认后执行。
> 调度完成后直接告知结果，**不需要用户确认**。
>
> 执行前确保已运行变量加载命令（见 `config.md`），使 `$MY_TODAY`、`$MY_WEEK` 等变量可用。

## 分组定义

| 分组 | 含义 |
|------|------|
| MY_WEEK | 下周要做、与主线直接相关的任务 |
| MY_MONTH | 本月目标范围内但不适合本周的任务 |
| MY_TODAY | 今天的任务（周度调度后不深入干预） |
| MY_UNPLANNED | 积压待处理，尚未纳入计划周期 |
| MY_WATCH | **你认为重要，但 AI 判断本周不应安排的任务** |

## 保持关注的边界（硬规则）

**MY_WATCH 只能从以下三个分组移入：**
- MY_TODAY
- MY_WEEK
- MY_MONTH

**禁止从 MY_UNPLANNED 移入 MY_WATCH。**

## 读取所有分组

```bash
# 分别对每个分组执行，使用已加载的环境变量
lark-cli task sections tasks --as user \
  --section-guid "$MY_TODAY" \
  --format json --page-all

lark-cli task sections tasks --as user \
  --section-guid "$MY_WEEK" \
  --format json --page-all

lark-cli task sections tasks --as user \
  --section-guid "$MY_MONTH" \
  --format json --page-all

lark-cli task sections tasks --as user \
  --section-guid "$MY_WATCH" \
  --format json --page-all
```

## 判断逻辑

以**下周主线**为核心，结合本月目标判断：

| 当前分组 | 与下周主线关系 | 与本月目标关系 | 目标分组 |
|---------|-------------|-------------|---------|
| MY_MONTH / MY_WATCH | 与主线直接相关 | — | → MY_WEEK |
| MY_UNPLANNED | 与主线直接相关 | — | → MY_WEEK |
| MY_WEEK / MY_TODAY | 与主线无关 | 属于月目标范围 | → MY_MONTH |
| MY_WEEK / MY_TODAY | 与主线无关 | 也与月目标无关 | → MY_WATCH |
| MY_MONTH | 与主线无关 | 也与月目标无关 | → MY_WATCH |
| MY_WEEK | 与主线直接相关 | — | 保留 |

**MY_WEEK 任务数量上限**：建议 ≤8 条（超出时优先保留与主线最直接相关的，其余移 MY_MONTH）。

**移入 MY_WATCH 时必须在输出中说明**：「你认为重要，但本周不应安排，原因是……」

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
📋 本周任务分组已调整

移入「本周计划」：{N} 条
移入「本月计划」：{N} 条
移入「保持关注」：{N} 条（仅来自今天/本周/本月计划）
  - 「{任务名}」（你认为重要，但本周不应安排：{原因}）

未动：{N} 条
```

若无任何移动，直接说「各分组任务与本周主线一致，无需调整」。
