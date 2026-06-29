# Monthly Goal · 任务分组调度（月度视角）

> 在守门四关通过、月度目标确认后执行。
> 调度完成后直接告知结果，**不需要用户确认**。

## 分组定义

| 分组 | 含义 |
|------|------|
| MY_MONTH | 本月内要做、但不一定本周的任务 |
| MY_WEEK | 本周要做的任务（月度调度后不深入干预） |
| MY_TODAY | 今天要做的任务（月度调度后不深入干预） |
| MY_UNPLANNED | 积压待处理，尚未纳入任何计划周期 |
| MY_WATCH | **你认为重要，但 AI 判断本月不应安排的任务** |

## 保持关注的边界（硬规则）

**MY_WATCH 只能从以下三个分组移入：**
- MY_TODAY
- MY_WEEK
- MY_MONTH

**禁止从 MY_UNPLANNED 移入 MY_WATCH。** 未安排的任务若不符合本月目标，留在未安排即可，不做降级。

## 读取所有分组

```bash
lark-cli task sections tasks --as user \
  --section-guid "<分组 GUID>" \
  --format json --page-all
```

对 MY_TODAY、MY_WEEK、MY_MONTH、MY_UNPLANNED、MY_WATCH 各执行一次。

## 判断逻辑

| 当前分组 | 与本月目标关系 | 目标分组 |
|---------|-------------|---------|
| MY_UNPLANNED | 明确属于本月目标范围 | → MY_MONTH |
| MY_UNPLANNED | 不符合本月目标 | **保留未安排，不动** |
| MY_WATCH | 明确属于本月目标范围 | → MY_MONTH |
| MY_WEEK / MY_TODAY | 与本月所有目标无关 | → MY_WATCH |
| MY_MONTH | 与本月所有目标无关 | → MY_WATCH |
| MY_MONTH / MY_WEEK / MY_TODAY | 属于本月目标范围 | 保留原分组不动 |

**「与本月目标有关」的判断标准（满足任一即可）：**
- 任务标题/内容直接对应某条目标的验收标准
- 任务属于本月目标所在领域（写作/产品/成长…）且不属于刻意不做清单
- 任务是推进本月目标的前置步骤

**移入 MY_WATCH 时必须在输出中说明**：「你认为重要，但本月不应安排，原因是……」

## 执行移动

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<task_guid>" \
  --section-guid "<目标分组 GUID>"
```


## 输出结果

```
📋 月度任务分组已调整

移入「本月计划」：{N} 条
  - 「{任务名}」（来自：未安排/保持关注）

移入「保持关注」：{N} 条（仅来自今天/本周/本月计划）
  - 「{任务名}」（你认为重要，但本月不应安排：{原因}）

未动：{N} 条
```

若无任何移动，直接说「各分组任务与本月目标一致，无需调整」。
