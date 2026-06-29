# Quick Task · API 调用

执行前 Read `Personal-os/references/config.md` 取 GUID。以下 `<变量>` 替换为 config 中的实际值。

## 1. 创建任务

```bash
lark-cli task +create --as user \
  --summary "<任务标题>" \
  --description "<描述，无则省略此参数>" \
  --due "<截止日期，无则省略此参数>" \
  --assignee "<USER_OPEN_ID>" \
  --json
```

从返回取 `data.guid` 作为 `task_guid`。

## 2. 加入清单并落入「未安排」

```bash
lark-cli task +tasklist-task-add --as user \
  --tasklist-id "<LIST_IDEA|WRITING|GROWING|ROUTINE>" \
  --task-id "<TASK_GUID>" \
  --section-guid "<MY_UNPLANNED>" \
  --json
```

`--section-guid` 若报 section 不存在，省略该参数重试（任务会落入清单默认分组）。

每条任务只加入一个清单。不使用 `LIST_PROJECTS`。
