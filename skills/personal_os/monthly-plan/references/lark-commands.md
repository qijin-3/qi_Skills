# Monthly Plan · 飞书 CLI 参考

**执行任何命令前必须先加载变量**：运行 `{PERSONAL_OS_ROOT}/references/config.md` 中「调什么命令（加载系统变量）」部分的 `eval "$(python3 ...)"` 命令，之后直接使用 `$FEISHU_BASE_TOKEN`、`$TABLE_MONTHLY` 等环境变量，**禁止手工从文件中抄值**。工作目录：`{PERSONAL_OS_ROOT}/`。

## 任务读取原则

**只读「我负责的」任务**，禁止全量搜索：

| 允许 | 禁止 |
|------|------|
| `lark-cli task +get-my-tasks` | `lark-cli task +search`（易超时） |
| `lark-cli task sections tasks` | 已废弃的 `+task-list`、`+section-task-list` |
| `lark-cli task tasklists tasks`（按清单） | 无 assignee 过滤的广域查询 |

---

## 读上月数据（Step 1 用）

```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<上月 YYYY-MM>" \
  --search-field "周期" \
  --format json --limit 20
```

---

## 读分组任务（Step 5 任务调度用）

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
```

## 移动任务

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "my_tasks" \
  --task-id "<task_guid>" \
  --section-guid "$MY_MONTH" \
  --format json
```

---

## 写入目标表（Step 6 用）

使用 `+record-upsert`（非已废弃的 `+record-create` / `+record-update`）。

**创建本月目标（写入 TABLE_MONTHLY，必须关联北极星支柱）：**

第一步：查询对应北极星支柱的 record_id：
```bash
lark-cli base +record-list --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_NORTH_STAR" \
  --format json --limit 10
# 从返回结果中找到对应支柱（内容杠杆/产品杠杆/能力复利）的 record_id
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

**创建 W1 周目标（必须关联所属月度目标）：**

第一步：查询本月月度目标的 record_id：
```bash
lark-cli base +record-search --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_MONTHLY" \
  --keyword "<YYYY-MM>" --search-field "周期" \
  --format json --limit 10
```

第二步：写入 W1 周目标：
```bash
lark-cli base +record-upsert --as user \
  --base-token "$FEISHU_BASE_TOKEN" \
  --table-id "$TABLE_WEEKLY" \
  --json '{
    "主线":"<W1 针对该目标的具体行动>",
    "周期":"<YYYY-W01>",
    "状态":"进行中",
    "领域":"<领域>",
    "所属月度目标":[{"id":"<月度目标 record_id>"}]
  }'
```

目标完成度为 0–1 小数（百分比 ÷ 100）。状态用「已达成」或「已调整」。
