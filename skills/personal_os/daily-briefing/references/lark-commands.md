# Daily Briefing · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_MONTHLY`、`$TABLE_WEEKLY` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

> **不写日志表**：早报不操作 `$TABLE_LOGS`。今日计划写入本地快照 `state/daily_snapshot_{YYYY-MM-DD}.json`，由 `evening-review` 统一 upsert 到日志表。

## 读分组任务

```bash
lark-cli task sections tasks --as user \
  --section-guid "<分组 GUID>" \
  --format json --page-all
```

对 MY_TODAY、MY_WEEK、MY_MONTH、MY_UNPLANNED、MY_WATCH 各执行一次。

## 读进行中目标

```bash
# 读本月月度目标
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10

# 读本周周目标
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_WEEKLY" \
  --keyword "<YYYY-Wnn>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10
```

## 移动任务（换分组）

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<task_guid>" \
  --section-guid "<目标分组 GUID>" \
  --format json
```

## 添加任务评论

```bash
lark-cli task +comment --as user \
  --task-id "<task_guid>" \
  --content "早报 {YYYY-MM-DD}：今天主攻这条，原因：{高杠杆/对齐目标/截止日等}" \
  --format json
```
