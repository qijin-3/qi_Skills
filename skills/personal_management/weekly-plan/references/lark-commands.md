# Weekly Goal · 飞书 CLI 参考

执行前 Read `Personal-os/references/config.md` 取变量。工作目录：`Personal-os/`。

## 读上周完成任务

```bash
lark-cli task +task-list --as user \
  --completed true \
  --complete-time-from "<上周一 00:00 Unix 毫秒>" \
  --complete-time-to "<上周日 23:59 Unix 毫秒>" \
  --format json
```

汇总：完成条数、清单分布（Writing/Growing/Projects/Routine/Idea）。

## 读日志表（上周完成率 + 主线推进）

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_LOGS>" \
  --filter '{"conjunction":"and","conditions":[
    {"field_name":"日期","operator":"isAfter","value":["ExactDate","<上周一>"]},
    {"field_name":"日期","operator":"isBefore","value":["ExactDate","<本周一>"]}
  ]}' \
  --format json
```

提取每天的 `今日任务完成度`（FIELD_LOG_COMPLETION_RATE）和 `主线推进情况`（FIELD_LOG_MAINLINE），计算均值和推进天数。

## 读本月进行中目标（动量检测用）

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_MONTHLY>" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10
```

## 读上周目标

```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_WEEKLY>" \
  --keyword "<YYYY-Wnn-1>" --search-field "周期" \
  --format json --limit 5
```

## 读上周/本月目标（动量检测用）

```bash
# 读本月进行中月度目标
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_MONTHLY>" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10

# 读上周周目标
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_WEEKLY>" \
  --keyword "<YYYY-Wnn-1>" --search-field "周期" \
  --format json --limit 5
```

## 更新上周目标（打分）

```bash
lark-cli base +record-upsert --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_WEEKLY>" \
  --record-id "<上周目标 record_id>" \
  --json '{"完成度": <0-1 小数>,"状态": "<已达成/已调整>"}'
```

- 分数换算：用户说的百分比 ÷ 100（如 75% → 0.75）
- 状态：≥0.8 → 已达成；<0.8 → 已调整

## 创建下周目标（每个活跃月度目标各一条）

> 每条活跃月度目标对应 TABLE_WEEKLY 中一条独立周记录，不合并。

第一步：查询本月月度目标 record_id（取所有进行中的条目）：
```bash
lark-cli base +record-search --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_MONTHLY>" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --format json --limit 10
```

第二步：为每个本周有行动的月度目标，分别写入一条周目标：
```bash
lark-cli base +record-upsert --as user \
  --base-token "<FEISHU_BASE_TOKEN>" \
  --table-id "<TABLE_WEEKLY>" \
  --json '{
    "主线":"<本周针对该目标的具体行动，一句话>",
    "周期":"<YYYY-Wnn>",
    "状态":"进行中",
    "领域":"<该目标领域>",
    "所属月度目标":[{"id":"<对应月度目标 record_id>"}]
  }'
```

若某月度目标本周无具体行动（如时机未到），不建记录。

