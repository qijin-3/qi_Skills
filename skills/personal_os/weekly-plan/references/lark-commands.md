# Weekly Plan · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_WEEKLY` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

## 读分组任务

```bash
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
  --section-guid "$MY_UNPLANNED" \
  --format json --page-all

lark-cli task sections tasks --as user \
  --section-guid "$MY_WATCH" \
  --format json --page-all
```

## 移动任务（换分组）

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<task_guid>" \
  --section-guid "$MY_WEEK" \
  --format json
```

替换 `$MY_WEEK` 为目标分组变量（`$MY_TODAY` / `$MY_WEEK` / `$MY_MONTH` / `$MY_WATCH`）。

## 读本月进行中月度目标

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10
```

## 创建下周目标（每个活跃月度目标各一条）

第一步：查询本月月度目标 record_id：
```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --format json --limit 10
```

第二步：为每个本周有行动的月度目标，分别写入一条周目标：
```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_WEEKLY" \
  --json '{
    "主线":"<本周针对该目标的具体行动，一句话>",
    "周期":"<YYYY-Wnn>",
    "状态":"进行中",
    "领域":"<该目标领域>",
    "所属月度目标":[{"id":"<对应月度目标 record_id>"}]
  }'
```
