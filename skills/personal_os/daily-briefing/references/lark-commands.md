# Daily Briefing · 飞书 CLI 参考

执行前解析 `PERSONAL_OS_ROOT`（探测顺序见 `{PERSONAL_OS_ROOT}/references/path-resolution.md`；父技能已解析则复用），再 Read `{PERSONAL_OS_ROOT}/references/config.md` 取变量。工作目录：`{PERSONAL_OS_ROOT}/`。

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
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_MONTHLY>" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10

# 读本周周目标
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_WEEKLY>" \
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

## 创建日志记录

```bash
lark-cli base +record-upsert --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
  --json '{"日期": <YYYY-MM-DD 的 Unix 毫秒时间戳>, "今日计划": "<任务1\n任务2\n任务3>"}'
```

## 查询日志记录（是否已存在）

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
  --keyword "<YYYY-MM-DD>" --search-field "日期" \
  --format json --limit 1
```

若已存在则 `+record-upsert --record-id <id>`，不存在则直接 `+record-upsert`（不带 record-id）。
