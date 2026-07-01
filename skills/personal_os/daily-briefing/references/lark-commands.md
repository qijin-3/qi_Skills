# Daily Briefing · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_LOGS` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

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

## 查询今日日志记录（写日志前必须先查）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --filter '{"conjunction":"and","conditions":[
    {"field_name":"日期","operator":"is","value":["ExactDate","<YYYY-MM-DD>"]}
  ]}' \
  --format json
```

**硬规则**：每天只允许一条日志记录。早报负责创建当日记录；若已存在则只更新，禁止新建第二条。

## 写日志表（upsert）

先执行上方查询，再按结果选择命令：

**0 条** → 创建（不带 `--record-id`）：

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --json '{"日期": <YYYY-MM-DD 的 Unix 毫秒时间戳>, "今日计划": "<任务1\n任务2\n任务3>"}'
```

**1 条** → 更新（必须带 `--record-id`，只写 `今日计划`）：

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --record-id "<record_id>" \
  --json '{"今日计划": "<任务1\n任务2\n任务3>"}'
```

**多条** → 优先选已有 `今日计划` 的那条；若都没有则选最早创建的。用其 `record_id` 更新 `今日计划`，并在输出中警告「今日日志表存在重复记录，请手动合并」。
