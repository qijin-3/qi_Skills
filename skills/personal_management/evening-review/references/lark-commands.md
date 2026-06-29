# Evening Review · 飞书 CLI 参考

执行前 Read `Personal-os/references/config.md` 取变量。工作目录：`Personal-os/`。

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
lark-cli task +section-task-list --as user \
  --section-guid "<MY_TODAY>" \
  --format json
```

从结果中过滤掉已完成的（`completed_at` 不为空），得到未完成任务列表。

## 读今日日志记录

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
  --filter '{"conjunction":"and","conditions":[
    {"field_name":"日期","operator":"is","value":["ExactDate","<YYYY-MM-DD>"]}
  ]}' \
  --format json
```

## 读最近2天日志（连续低完成率检查）

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
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
  --section-guid "<MY_WEEK>" \
  --format json
```

## 更新日志表（晚报核心写入）

```bash
lark-cli base +record-update --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
  --record-id "<今日 record_id>" \
  --json '{"fields":{
    "今日完成任务": "<完成任务1\n完成任务2>",
    "今日任务完成度": <0-1小数，如0.67>,
    "主线推进情况": "<推进 / 部分推进 / 未推进>",
    "说明": "<主线推进依据一句话>",
    "日记路径": "content/<YYYY>/<MM>/diary.md"
  }}'
```

字段说明：
- `今日任务完成度`（FIELD_LOG_COMPLETION_RATE）：完成数 / 计划数，0–1 小数
- `主线推进情况`（FIELD_LOG_MAINLINE）：单选，来自主线判断
- `说明`（FIELD_LOG_NOTE）：文本，一句依据
- `日记路径`（FIELD_LOG_DIARY_PATH）：diary-assembler 写入后读取

