# Monthly Review · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_MONTHLY` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

## 任务读取原则

**只读「我负责的」任务**，禁止全量搜索：

| 允许 | 禁止 |
|------|------|
| `lark-cli task +get-my-tasks` | `lark-cli task +search`（易超时） |
| `lark-cli task tasklists tasks`（按清单，见下） | 无 assignee 过滤的广域查询 |

---

## 1a. 上月完成任务统计

### 第一步：拉取我负责的已完成任务

```bash
lark-cli task +get-my-tasks --as user \
  --complete=true \
  --format json \
  --page-all
```

通常 <100 条，数秒内返回。列表项含 `guid`、`summary`、`created_at`（**不含** `completed_at`）。

### 第二步：按完成时间筛上月（本地过滤）

对返回的每条 `guid` 取详情，用 `completed_at` 判断是否落在上月区间内：

```bash
lark-cli task tasks get --as user \
  --task-guid "<TASK_GUID>" \
  --format json
```

上月区间（Unix 毫秒，本地时区）：

- 起始：上月 1 日 00:00:00
- 结束：上月最后一日 23:59:59

Mac 计算示例：

```bash
date -j -f "%Y-%m-%d %H:%M:%S" "2026-06-01 00:00:00" "+%s" | awk '{print $1*1000}'
```

若已完成任务总数 >80，可只统计总数并在复盘中注明「未逐条核对完成月份」。

### 第三步：按清单分布

从 `tasks get` 返回的 `tasklists[].tasklist_guid` 对照 `$LIST_*` 变量归类：

| 变量 | 清单 |
|------|------|
| `$LIST_IDEA` | 💡 Idea |
| `$LIST_WRITING` | ✍️ Writing |
| `$LIST_GROWING` | ♻️ Growing |
| `$LIST_PROJECTS` | 📦 Projects |
| `$LIST_ROUTINE` | 🔁 Routine |

---

## 1b. 日志表 · 今天要做完成率

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_LOGS" \
  --keyword "<上月 YYYY-MM>" \
  --search-field "日期" \
  --filter-json '{"logic":"and","conditions":[
    ["日期",">","<上月1日 YYYY-MM-DD>"],
    ["日期","<","<本月1日 YYYY-MM-DD>"]
  ]}' \
  --format json --limit 50
```

从记录计算每日完成率均值；数据不足时如实说明，不编造。

---

## 1c. 上月目标

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM-1>" \
  --search-field "周期" \
  --format json --limit 20
```

同时 Read 本地 `content/{YYYY}/{MM-1}/monthly-plan.md` 作对照（本地常为权威来源）。

---

## 写入目标表

使用 `+record-upsert`（非已废弃的 `+record-create` / `+record-update`）。

**更新上月目标（打分归档）：**

```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --record-id "<record_id>" \
  --json '{"目标完成度":0.45,"状态":"已调整"}'
```

**创建本月目标（写入 TABLE_MONTHLY，必须关联北极星支柱）：**

第一步：查询对应北极星支柱的 record_id：
```bash
lark-cli base +record-list --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_NORTH_STAR" \
  --format json --limit 10
# 从返回的 record_id_list 中找到对应支柱（内容杠杆/产品杠杆/能力复利）的 ID
```

第二步：写入月度目标，同时填关联字段：
```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --json '{
    "目标":"<目标描述>",
    "周期":"<YYYY-MM>",
    "状态":"进行中",
    "领域":"<产品/写作/成长/健康/财务>",
    "验收标准":"<30秒内能判断的标准>",
    "北极星支柱":[{"id":"<北极星支柱 record_id>"}]
  }'
```

**更新目标打分（月度）：**
```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --record-id "<record_id>" \
  --json '{"目标完成度":<0-1小数>,"状态":"<已达成/已调整>"}'
```

目标完成度为 0–1 小数（百分比 ÷ 100）。状态用「已达成」或「已调整」。
