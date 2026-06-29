---
name: diary-capture
version: 1.0.0
description: >
  日记碎片捕获入口。用户发来感受、反思、见闻、吐槽、生活记录、今天发生的事时立即触发。
  只要消息是描述性/叙述性句子（不是任务/待办），就走本技能。
  原文零改写存入本地 pending 文件，不拼装、不分析、不评论。
  用户说"记录一下"、"日记"、"今天XXX"、"#日记"时也触发。
  与 quick-task 互斥：纯感受/见闻 → diary-capture；有行动意图 → quick-task。
---

# Diary Capture

收到日记碎片 → 原文写入本地 pending → 短回复"记下了。"

## 开始前

Read `Personal-os/references/config.md`，取 `PATH_DIARY_PENDING`。

## 触发判断（与 quick-task 互斥）

**满足任意一条 → 走本技能：**

1. 用户有显式日记标记：`#日记`、`记录一下`、`记一下`、`日记`
2. 非行动句式：描述感受 / 反思 / 见闻 / 今日回顾，句中无"要做 / 帮我 / 记得做 / 待办"等行动词
3. 同一天已有 ≥1 条 pending 碎片，且当前消息看起来是同一情境的延续

**以下走 quick-task，不走本技能：**

- 明确的行动意图（"帮我建个任务"、"记得做 X"、"要做 Y"）
- 有可执行的动词 + 明确宾语，无感受描述

**模糊时**：倾向于 diary-capture（保留原文比漏捕获更重要）。

## 工作流

### 1. 确定路径

计算今日日期 `YYYY-MM-DD`，构造路径：

```
Personal-os/state/diary_pending_{YYYY-MM-DD}.json
```

若 `Personal-os/state/` 目录不存在，先创建。

### 2. 读取现有 pending 文件

若文件存在，读取现有数组；若不存在，初始化为空数组 `[]`。

### 3. 追加新条目

```json
{
  "time": "HH:mm",
  "text": "用户原话，一字不改",
  "source": "飞书私聊"
}
```

**禁止改写 `text` 字段**：不总结、不修正语法、不加标点、不扩展内容。

### 4. 写回文件

将新数组写回 `diary_pending_{YYYY-MM-DD}.json`。

### 5. diary_session 状态更新

读取 `Personal-os/state/diary_session.json`（不存在则 `{}`）：

- 若今日条目数 ≥ 2 → 设 `diary_mode: true`、`last_entry: "<当前时间>"`
- 若 < 2 → 设 `diary_mode: false`

写回文件。

### 6. 回复用户

```
记下了。
```

仅此一句，不分析内容，不追问，不提建议。


## 错误处理

- 文件写入失败 → 回复"记录失败，请再发一次。"，不沉默
- 不确定是日记还是任务 → 默认走 diary-capture，并在回复末加："（如果是任务请说'帮我建个任务'）"
