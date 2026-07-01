# Evening Review · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_LOGS` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

## 读今日完成任务

```bash
lark-cli task +task-list --as user \
  --completed true \
  --complete-time-from "<今日 00:00 Unix 毫秒>" \
  --complete-time-to "<今日 23:59 Unix 毫秒>" \
  --format json
```

提取：guid、summary、completed_at。

**硬规则**：以 `completed_at` 时间戳为唯一数据源，不以"分组中是否有任务"代替。

## 读当日分组任务（未完成项）

```bash
lark-cli task sections tasks --as user \
  --section-guid "$MY_TODAY" \
  --format json --page-all
```

从结果中过滤掉已完成的（`completed_at` 不为空），得到未完成任务列表。

## 读今日日志记录（Step 2 / Step 7 共用）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --filter '{"conjunction":"and","conditions":[
    {"field_name":"日期","operator":"is","value":["ExactDate","<YYYY-MM-DD>"]}
  ]}' \
  --format json
```

**硬规则**：晚报只更新早报创建的当日记录，禁止新建第二条。若查询到多条，优先选有 `今日计划` 的那条。

## 读最近2天日志（连续低完成率检查）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --filter '{"conjunction":"and","conditions":[
    {"field_name":"日期","operator":"isAfter","value":["ExactDate","<前天日期>"]},
    {"field_name":"日期","operator":"isBefore","value":["ExactDate","<明天日期>"]}
  ]}' \
  --format json
```

提取 `今日任务完成度`（FIELD_LOG_COMPLETION_RATE）字段值，判断是否连续 ≥2 天 < 0.33。

## 添加任务评论

```bash
lark-cli task +comment --as user \
  --task-id "<guid>" \
  --content "晚报 {YYYY-MM-DD}：今天未完成。原因待跟踪。" \
  --format json
```

## 移动任务（未完成项处理）

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<guid>" \
  --section-guid "$MY_WEEK" \
  --format json
```

## 更新日志表（晚报核心写入）

先执行「读今日日志记录」查询，再按结果选择：

**1 条（正常）** → 带 `record_id` 更新晚报字段，**禁止**不带 `record_id` 的 upsert：

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --record-id "<今日 record_id>" \
  --json '{
    "今日完成任务": "<完成任务1\n完成任务2>",
    "今日任务完成度": <0-1小数，如0.67>,
    "主线推进情况": "<推进 / 部分推进 / 未推进>",
    "说明": "<主线推进依据一句话>"
  }'
```

**0 条（早报未运行）** → 创建当日唯一记录，同时写入日期与晚报字段：

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --json '{
    "日期": <YYYY-MM-DD 的 Unix 毫秒时间戳>,
    "今日完成任务": "<完成任务1\n完成任务2>",
    "今日任务完成度": <0-1小数，如0.67>,
    "主线推进情况": "<推进 / 部分推进 / 未推进>",
    "说明": "<主线推进依据一句话>"
  }'
```

**多条** → 选有 `今日计划` 的那条（或最早一条）更新，警告用户合并重复记录。

字段说明：
- `今日任务完成度`（FIELD_LOG_COMPLETION_RATE）：完成数 / 计划数，0–1 小数
- `主线推进情况`（FIELD_LOG_MAINLINE）：单选，来自主线判断
- `说明`（FIELD_LOG_NOTE）：文本，一句依据
