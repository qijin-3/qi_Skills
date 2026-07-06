# Weekly Review · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_WEEKLY` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

## 读上周完成任务

```bash
lark-cli task +get-my-tasks --as user \
  --complete=true \
  --format json \
  --page-all
```

返回后本地按 `completed_at` 筛出落在上周区间的任务。汇总：完成条数、清单分布（Writing/Growing/Projects/Routine/Idea）。

## 读日志表（上周完成率 + 主线推进）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
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
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --filter-json '{"logic":"and","conditions":[["状态","==","进行中"]]}' \
  --format json --limit 10
```

## 读上周目标（Step 1d / Step 7 共用）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_WEEKLY" \
  --keyword "<YYYY-Wnn-1>" --search-field "周期" \
  --format json --limit 10
```

**必须保留**返回的每条 `record_id` 与 `主线` 字段，供 Step 4 打分与 Step 7 归档使用。周期格式示例：`2026-W26`。

## 归档上周目标（Step 7 必须执行）

对 Step 1d 返回的**每一条**记录执行 upsert。**必须带 `record_id`**，禁止新建：

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_WEEKLY" \
  --record-id "<上周目标 record_id>" \
  --json '{
    "完成度": <0-1小数>,
    "状态": "<已达成/已调整>",
    "总结": "<该主线的周复盘小结，≤150字>"
  }'
```

字段说明：
- `完成度`：Step 4 最终分数 ÷ 100（如 75% → 0.75）
- `状态`：完成度 ≥0.8 → `已达成`；<0.8 → `已调整`
- `总结`：针对该条 `主线` 的周复盘小结（完成情况 + 偏离/收获 + 改进点）

**硬规则**：
- 同周 N 条记录须逐条 upsert，不得漏更新
- 禁止不带 `record_id` 的 upsert（创建下周目标由 `weekly-plan` 负责，不在本技能）
- Step 1d 返回 0 条时可跳过，输出注明即可
