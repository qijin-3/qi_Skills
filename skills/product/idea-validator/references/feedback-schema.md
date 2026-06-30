# User Feedback Schema · 用户反馈数据结构

## 文件格式

`user-feedback.jsonl` — [JSON Lines](https://jsonlines.org/) 格式，每行一条独立的 JSON 记录。

**优点**：
- **追加友好**：`echo '{...}' >> user-feedback.jsonl`，无需重写整个文件
- **分析友好**：`jq`、pandas、Excel Power Query、DuckDB 均原生支持
- **增量复用**：多次调研的数据可累积在同一文件，按 `session_date` 区分批次

文件路径：`/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/user-feedback.jsonl`

---

## 字段定义

### 基础标识字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | string | ✅ | 唯一 ID，格式：`<platform>-<4位序号>`，如 `reddit-0042` |
| `idea_slug` | string | ✅ | idea 的 URL-safe 标识，如 `ai-writing-tool` |
| `idea_name` | string | ✅ | idea 的展示名称，如 `AI 写作助手` |
| `session_date` | string (ISO) | ✅ | 本次调研日期，格式 `YYYY-MM-DD` |

### 来源字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `source_platform` | string | ✅ | 来源平台枚举：`reddit` \| `twitter` \| `xiaohongshu` \| `app_store` \| `google_play` \| `github` \| `hacker_news` \| `youtube` \| `bilibili` \| `g2` \| `producthunt` \| `capterra` \| `other` |
| `source_url` | string \| null | ✅ | 原始页面可访问 URL；登录墙内容填 `null` |
| `source_type` | string | ✅ | 内容类型枚举：`post` \| `comment` \| `review` \| `issue` \| `discussion` \| `video_comment` \| `tweet` \| `reply` |
| `source_region` | string | ✅ | 内容来源区域：`cn`（中文/国内）\| `global`（英文/海外）|

### 内容字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `content` | string | ✅ | 原始引用文本（保留原文，不改写）|
| `content_zh` | string | ✅ | 中文翻译。`language` 为 `zh` 时与 `content` 相同；`en` / `other` 时填写准确中文译文 |
| `language` | string | ✅ | 内容语言：`zh` \| `en` \| `other` |
| `search_query` | string | ✅ | 触发找到该条内容的搜索词，用于追溯和复用 |

### 分析字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `sentiment_type` | string | ✅ | 情绪类型枚举：`pain`（痛苦词）\| `workaround`（妥协词）\| `wish`（期望词）\| `willingness_to_pay`（付费词）|
| `credibility` | string | ✅ | 可信度：`high`（有 URL + 互动数据）\| `medium`（有来源但需登录或转述）\| `low`（无来源或无法核实）|
| `hypothesis_dimension` | string | ✅ | 关联的 Lean Hypothesis 字段枚举：`target_user`（目标用户）\| `trigger_scene`（触发场景）\| `pain_point`（核心痛点）\| `alternative`（现有替代）\| `differentiation`（差异化方向）\| `validation_signal`（验证信号）\| `unexpected`（意外发现）|

### 时效字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `published_at` | string \| null | ✅ | 内容发布时间；精确到日期时填 `YYYY-MM-DD`，精确到月时填 `YYYY-MM`，无法确定时填 `null` |
| `is_recent` | boolean | ✅ | 是否在采集日期的 6 个月内发布；`true` = 主力证据，`false` = 降权辅助证据 |

### 竞品与互动字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `competitors_mentioned` | string[] | — | 内容中提到的竞品名称列表，无则填 `[]` |
| `engagement` | object \| null | — | 互动数据；格式见下，无法获取时填 `null` |
| `engagement.upvotes` | number \| null | — | 点赞/投票数 |
| `engagement.comments` | number \| null | — | 评论数 |
| `engagement.views` | number \| null | — | 浏览量（适用于 YouTube/B站） |

---

## 完整模板示例

```jsonl
{"id":"reddit-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"reddit","source_url":"https://www.reddit.com/r/writing/comments/abc123/comment/xyz","source_type":"comment","source_region":"global","content":"I've been using Notion AI for drafts but it keeps hallucinating facts. I had to spend 30 minutes fact-checking a 500-word blog post. This defeats the entire purpose.","content_zh":"我用 Notion AI 写草稿，但它老是编造事实。一篇 500 字的博文，我花了 30 分钟核对事实。这完全失去了意义。","language":"en","search_query":"notion AI writing frustrating","sentiment_type":"pain","credibility":"high","hypothesis_dimension":"pain_point","published_at":"2026-05-18","is_recent":true,"competitors_mentioned":["Notion AI"],"engagement":{"upvotes":89,"comments":14,"views":null}}
{"id":"xiaohongshu-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"xiaohongshu","source_url":null,"source_type":"comment","source_region":"cn","content":"用了三个月的某 AI 写作工具，最大的问题是风格太统一，写出来的东西都有 AI 味，被编辑打回来好几次","content_zh":"用了三个月的某 AI 写作工具，最大的问题是风格太统一，写出来的东西都有 AI 味，被编辑打回来好几次","language":"zh","search_query":"AI写作工具 踩雷","sentiment_type":"pain","credibility":"medium","hypothesis_dimension":"pain_point","published_at":"2026-04","is_recent":true,"competitors_mentioned":[],"engagement":{"upvotes":203,"comments":null,"views":null}}
{"id":"app_store-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"app_store","source_url":"https://apps.apple.com/us/app/id123456789","source_type":"review","source_region":"global","content":"1 star. The app deleted my 3000-word draft because it crashed mid-sync. No backup. Switching to something else immediately.","content_zh":"一星。同步中途崩溃，App 删掉了我的 3000 字草稿，没有备份。马上换别的了。","language":"en","search_query":"app store ai writing 1 star review","sentiment_type":"pain","credibility":"high","hypothesis_dimension":"pain_point","published_at":"2026-06-01","is_recent":true,"competitors_mentioned":[],"engagement":{"upvotes":null,"comments":null,"views":null}}
{"id":"youtube-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"youtube","source_url":"https://www.youtube.com/watch?v=abc&lc=xyz","source_type":"video_comment","source_region":"global","content":"I wish there was an AI tool that could match my existing writing style instead of generating generic corporate speak. Does anyone know if this exists?","content_zh":"希望有 AI 工具能匹配我现有的写作风格，而不是生成千篇一律的企业腔。有人知道有这种产品吗？","language":"en","search_query":"youtube best ai writing tool 2026","sentiment_type":"wish","credibility":"medium","hypothesis_dimension":"differentiation","published_at":"2026-05","is_recent":true,"competitors_mentioned":[],"engagement":{"upvotes":47,"comments":null,"views":null}}
{"id":"bilibili-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"bilibili","source_url":"https://www.bilibili.com/video/BVxxx","source_type":"video_comment","source_region":"cn","content":"这个工具写公众号文章还行，但标题党味太重，发出去阅读量反而下降了","content_zh":"这个工具写公众号文章还行，但标题党味太重，发出去阅读量反而下降了","language":"zh","search_query":"AI写作工具 踩坑","sentiment_type":"pain","credibility":"medium","hypothesis_dimension":"pain_point","published_at":"2026-05","is_recent":true,"competitors_mentioned":[],"engagement":{"upvotes":128,"comments":null,"views":null}}
{"id":"github-0001","idea_slug":"ai-writing-tool","idea_name":"AI 写作助手","session_date":"2026-06-23","source_platform":"github","source_url":"https://github.com/writingai/app/issues/234","source_type":"issue","source_region":"global","content":"Feature request: support for custom style guides. I've been pasting the same 500-word style doc at the start of every session for months. This is ridiculous.","content_zh":"功能请求：支持自定义风格指南。好几个月了，每次会话开头我都要粘贴同一份 500 字的风格文档。太离谱了。","language":"en","search_query":"gh search issues ai writing style guide","sentiment_type":"wish","credibility":"high","hypothesis_dimension":"differentiation","published_at":"2026-03-22","is_recent":true,"competitors_mentioned":[],"engagement":{"upvotes":null,"comments":12,"views":null}}
```

---

## 使用指南

### 追加新条目
```bash
# 追加一条新记录（每次调研结束后自动执行）
echo '{"id":"reddit-0042",...}' >> "/Users/jin/SynologyDrive/Working/Ideas/ai-writing-tool/user-feedback.jsonl"
```

### 用 jq 分析

```bash
FILE="/Users/jin/SynologyDrive/Working/Ideas/ai-writing-tool/user-feedback.jsonl"

# 统计各平台条数
jq -s 'group_by(.source_platform) | map({platform: .[0].source_platform, count: length})' $FILE

# 筛选高可信度 + 最近 6 个月
jq 'select(.credibility == "high" and .is_recent == true)' $FILE

# 按情绪类型分组统计
jq -s 'group_by(.sentiment_type) | map({type: .[0].sentiment_type, count: length})' $FILE

# 查看所有提到某竞品的反馈
jq 'select(.competitors_mentioned | contains(["Notion"]))' $FILE

# 导出为 CSV（需要 jq 1.6+）
jq -r '[.id, .source_platform, .sentiment_type, .credibility, .published_at, .content, .content_zh] | @csv' $FILE
```

### 用 Python/pandas 分析

```python
import pandas as pd

df = pd.read_json(
    "/Users/jin/SynologyDrive/Working/Ideas/ai-writing-tool/user-feedback.jsonl",
    lines=True
)

# 时效性分析
df["is_recent"].value_counts()

# 平台 × 情绪类型交叉表
pd.crosstab(df["source_platform"], df["sentiment_type"])

# 高可信度证据
high_cred = df[df["credibility"] == "high"].sort_values("published_at", ascending=False)
```

### 多次调研合并

同一 `idea_slug` 的多次调研写入同一文件，用 `session_date` 区分批次：
```bash
# 查看各次调研收集量
jq -s 'group_by(.session_date) | map({date: .[0].session_date, count: length})' $FILE
```

---

## 元数据文件

每个 `<idea-slug>/` 目录同时包含 `feedback-meta.json`，记录调研元信息：

```json
{
  "idea_slug": "ai-writing-tool",
  "idea_name": "AI 写作助手",
  "sessions": [
    {
      "session_date": "2026-06-23",
      "target_region": "global",
      "enabled_platforms": ["reddit", "twitter", "app_store", "google_play", "github", "hacker_news", "youtube"],
      "skipped_platforms": [
        {"platform": "xiaohongshu", "reason": "目标用户为海外用户"},
        {"platform": "bilibili", "reason": "目标用户为海外用户"}
      ],
      "total_entries": 103,
      "high_credibility": 58,
      "medium_credibility": 45,
      "entries_recent_6m": 91
    }
  ]
}
```
