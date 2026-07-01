# 日记拼装逻辑

> 由 evening-review 的 Step 6（Mode A）或 Mode B 调用。
> 变量已由调用方读取 config.md 获得，此处直接引用。

---

## 步骤

### 1. 读取 pending 文件

路径：`{PERSONAL_OS_ROOT}/state/diary_pending_{YYYY-MM-DD}.json`

若文件不存在或为空数组 → 输出"今日暂无日记碎片。"，退出拼装。

### 2. 质量预检

随机抽取 min(3, 全部) 条，确认 `text` 字段为原始字符串（非空、非 null）。  
预检失败 → 不写文件，报错退出："pending 数据异常，请人工检查。"

### 3. 构造当日日记节

按 `time` 字段**倒序**排列（最新的在上），去掉 `text` 字符级完全重复的连续条目：

```markdown
---

## YYYY-MM-DD（周X）

**HH:mm**
用户原话

**HH:mm**
用户原话
```

- `**HH:mm**` 单独一行，加粗
- 紧接原文（`text`），不加任何注释或 AI 语言
- 每条之间空一行
- 周几根据日期计算（周一/周二/.../周日）

### 4. 插入 diary.md

目标路径：`{PERSONAL_OS_ROOT}/content/{YYYY}/{MM}/diary.md`

若文件不存在，先创建：

```markdown
# {YYYY}-{MM} 日记

```

**插入位置**：文件标题行之后、已有内容之前（新日期始终在最上方）。

### 5. 质量自检

从写入的 diary.md 中读取刚插入的今日节，与 pending 随机抽 3 条（或全部）做字符级比对：

- 不一致 → **回滚**（恢复 diary.md 原内容），不清空 pending，报错："日记写入校验失败，pending 保留，请人工检查。"
- 一致 → 继续

### 6. 清空 pending

将 `diary_pending_{YYYY-MM-DD}.json` 写为空数组 `[]`。  
同时更新 `state/diary_session.json`：设 `diary_mode: false`。

---

## 格式约束

| 允许 | 禁止 |
|------|------|
| 按时间倒序排列 | 改写任何 `text` 内容 |
| 去掉字符级完全重复的连续条目 | 总结、合并、删减 |
| 空行分段 | 加 AI 观点或情绪解读 |
