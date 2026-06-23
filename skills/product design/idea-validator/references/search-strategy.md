# Pain-Driven Search Framework · 搜索策略

## 核心原则

不搜话题，搜情绪。「productivity app」找到的是评测文章；「I hate my task manager because」找到的是真实用户痛点。目标是找到用户在没有人付钱让他们说好话时的真实声音。

**搜索词质量判断标准**：好的搜索词触发的结果情绪是「愤怒 > 失望 > 轻微不满」，而不是「这个产品不错」。

---

## 搜索词矩阵生成规则

基于锁定的 Lean Hypothesis，按四类生成搜索词，**每类至少生成 3 组，中英文各有**：

### 痛苦词（Pain Words）
**目的**：找真实抱怨，验证痛点存在且强烈

英文模板：
- `[产品类别] frustrating`
- `[产品类别] hate`
- `[产品类别] broken`
- `why does [产品类别] suck`
- `[竞品名] problems`
- `[竞品名] issues`

中文模板：
- `[产品类别] 太难用了`
- `[竞品名] 有什么问题`
- `[产品类别] 踩雷`
- `[竞品名] 吐槽`

### 妥协词（Workaround Words）
**目的**：找用户的 workaround，证明需求真实存在但没有被好好满足

英文模板：
- `instead of [竞品名] I use`
- `switched from [竞品名] to`
- `[产品类别] workaround`
- `[产品类别] alternative`
- `[竞品名] replacement`

中文模板：
- `代替 [竞品名]`
- `[产品类别] 替代方案`
- `[竞品名] 平替`

### 期望词（Wish Words）
**目的**：找未被满足的需求方向，这些往往是差异化切入点

英文模板：
- `wish [产品类别] could`
- `[产品类别] feature request`
- `if only [竞品名]`
- `[产品类别] needs to`

中文模板：
- `希望 [产品类别] 能`
- `[产品类别] 什么时候能支持`

### 付费词（Willingness-to-Pay Words）
**目的**：验证付费意愿，独立开发场景最关键的信号

英文模板：
- `worth paying for [产品类别]`
- `best paid [产品类别]`
- `[产品类别] pricing`
- `[竞品名] too expensive`（说明有付费行为，但对价格敏感）
- `[竞品名] worth it`

中文模板：
- `[产品类别] 收费`
- `[产品类别] 付费值不值`

**判断原则**：有人在讨论「值不值得付费」比「免费方案够用」更有价值，说明市场已有付费习惯。

---

## 平台定向搜索策略

### Reddit（最高价值平台）

**用户表达特点**：说真话，情绪真实，评论区比帖子本身更有价值，高赞评论 = 多数用户共鸣。

**工具命令**：`opencli reddit search "query"`
**降级**：Exa 全网搜索 `exa search "site:reddit.com query"`
**时间窗口**：优先最近 **6 个月**内的帖子

**搜索策略**：
- 找 rant 帖：`[竞品名] sucks` / `frustrated with [产品类别]`
- 找推荐帖：`what do you use for [产品类别]` / `best tool for [场景]`
- 找迁移帖：`switched from [竞品名]` / `looking for [竞品名] alternative`
- 优先查看：r/productivity、r/SaaS、r/Entrepreneur、r/smallbusiness，以及垂直领域 subreddit

**重点**：进帖子后看评论区，不只看帖子本身。高赞评论里的抱怨比帖子更有价值。

---

### X / Twitter

**用户表达特点**：实时情绪，适合找紧迫性信号；短文本情绪密度高。

**工具命令**：`twitter search "query"`
**降级**：Exa 全网搜索
**时间窗口**：优先最近 **6 个月**内

**搜索策略**：
- 带情绪词：`[竞品名] is broken` / `[产品类别] is trash`
- 找切换宣告：`finally switched from [竞品名]` / `done with [竞品名]`
- 找求推荐：`anyone know a good [产品类别]` / `looking for [产品类别] recommendations`

---

### 小红书

**用户表达特点**：中文市场核心平台，「避坑」类内容生态成熟；评论区比正文更真实，评论里的「求推荐 X」往往是直接需求信号。

**工具命令**：`opencli xiaohongshu search "query"`
**降级**：Exa 全网搜索
**时间窗口**：优先最近 **3 个月**内

**搜索策略**：
- 避坑方向：`[产品类别] 避坑` / `[竞品名] 踩雷`
- 推荐方向：`好用的 [产品类别]` / `[产品类别] 推荐`（重点看评论区的反对意见）
- 直接抱怨：`[竞品名] 不好用` / `[产品类别] 有没有更好的`

---

### App Store（必须执行，无需配置）

**用户表达特点**：1–2 星评论是最直接的产品缺陷清单，用户会写出竞品解决不了的具体问题；「功能缺失类抱怨」是找差异化最有价值的来源。

**两步访问法**：

第一步：用 iTunes Search API 找竞品 App ID
```bash
curl "https://itunes.apple.com/search?term=[竞品名]&entity=software&limit=5&country=us"
```
返回 JSON，提取 `trackId` 字段即为 App ID。

第二步：用 Jina Reader 读取竞品评论页
```bash
curl "https://r.jina.ai/https://apps.apple.com/us/app/id[APP_ID]"
# 或中国区：
curl "https://r.jina.ai/https://apps.apple.com/cn/app/id[APP_ID]"
```

**时间窗口**：优先最近 **3 个月**内的评论
**重点提取**：
- 「功能缺失」类（用户想要但没有）
- 「价格」类（付费意愿参照）
- 「替代方案」类（用户主动提到的竞品）

---

### Google Play（必须执行，无需配置）

**用户表达特点**：与 App Store 类似，1–2 星评论是缺陷清单；安卓用户偏好与 iOS 可能不同，需单独覆盖，不可只用 App Store 代替。

**两步访问法**：

第一步：搜索竞品，提取包名（`id=com.xxx`）
```bash
# 方式 A：Jina Reader（优先）
curl "https://r.jina.ai/https://play.google.com/store/search?q=[竞品名]&c=apps&hl=en"

# 方式 B：直接抓取（Jina 不可用时）
curl -sL "https://play.google.com/store/search?q=[竞品名]&c=apps&hl=en" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
# 从 HTML 提取 details?id=com.xxx.xxx
```

第二步：读取竞品详情页（含评论）
```bash
# 方式 A：Jina Reader（优先）
curl "https://r.jina.ai/https://play.google.com/store/apps/details?id=[包名]&hl=en&gl=us"

# 方式 B：直接抓取（降级）
curl -sL "https://play.google.com/store/apps/details?id=[包名]&hl=en&gl=us" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
```

**时间窗口**：优先最近 **3 个月**内的 1–2 星评论
**重点提取**：
- 「功能缺失」类（用户想要但没有）
- 「价格 / 订阅」类（付费意愿参照）
- 「崩溃 / 卡顿」类（产品稳定性痛点）
- 「替代方案」类（用户主动提到的竞品）

---

### GitHub（必须执行，需 gh CLI）

**用户表达特点**：开发者工具、开源竞品的核心社区；Issues 含真实 Bug 抱怨与功能请求，Discussions 有使用心得与迁移讨论；高 star + 高 open issues 说明用户活跃但需求未被满足。

**工具命令**（Agent-Reach 基础安装含 gh CLI，无需额外配置）：

```bash
# 搜 Issues / PR（痛点、功能请求、迁移讨论）
gh search issues "[竞品名] frustrating" --limit 20 \
  --json title,url,body,commentsCount,createdAt
gh search issues "[产品类别] feature request" --limit 20
gh search issues "alternative to [竞品名]" --limit 20

# 搜开源竞品仓库
gh search repos "[产品类别] tool" --limit 10 \
  --json fullName,description,url,stargazersCount,openIssuesCount

# 读特定竞品仓库 Issues（已知 org/repo 时）
gh issue list --repo [org]/[repo] --state all --limit 30 \
  --json title,url,body,comments,labels
gh api repos/[org]/[repo]/discussions --paginate 2>/dev/null || true
```

**Jina 降级**（补充读公开 Issues 页）：
```bash
curl "https://r.jina.ai/https://github.com/[org]/[repo]/issues"
curl "https://r.jina.ai/https://github.com/[org]/[repo]/discussions"
```

**GitHub API 降级**（无 gh 时）：
```bash
curl "https://api.github.com/search/issues?q=[竞品名]+frustrating&sort=comments&per_page=10"
```

**时间窗口**：优先最近 **12 个月**内
**搜索策略**：
- 对 Step 2/3 已识别的竞品，直接读其 GitHub 仓库 Issues（按 comments 排序）
- 搜索迁移讨论：`migrating from [竞品名]` / `switched from [竞品名]`
- 搜索功能缺口：`label:enhancement [痛点关键词]` / `is:issue is:open [功能名]`
- 开源竞品的高互动 Issue 往往直接暴露差异化机会

**重点**：Issue 正文 + 评论区的用户原话，比 README 营销文案更有价值。

---

### Hacker News（无需配置）

**用户表达特点**：技术类产品高价值平台，决策者和早期采纳者聚集，讨论深度高，「Ask HN」帖子通常能找到正在寻找解决方案的目标用户。

**工具命令**：
```bash
# 搜索故事
curl "https://hn.algolia.com/api/v1/search?query=[产品类别]&tags=story"
# 搜索评论
curl "https://hn.algolia.com/api/v1/search?query=[产品类别]&tags=comment"
# 按时间排序
curl "https://hn.algolia.com/api/v1/search_by_date?query=[产品类别]&tags=story"
```

**时间窗口**：最近 **12 个月**内
**搜索策略**：
- 搜索 `Ask HN: What do you use for [产品类别]`
- 搜索 `[竞品名] Show HN`（看评论区的质疑和功能讨论）

---

### G2 / Capterra / ProductHunt（B2B 产品补充执行）

**访问命令**：通过 Jina Reader 读取
```bash
curl "https://r.jina.ai/https://www.g2.com/products/[产品slug]/reviews"
curl "https://r.jina.ai/https://www.producthunt.com/posts/[产品slug]"
```

**策略**：
- G2 / Capterra：直接看竞品的 Cons 栏，提取高频词
- ProductHunt：看评论区「what's missing」类问题的回答
- 关注评分两极分化的竞品（4 星以上但有大量 1–2 星）

---

## 平台降级处理

当 Reddit / X / 小红书 未通过 Agent-Reach 配置时：

```bash
# Exa 全网搜索（替代）
exa search "[竞品名] problems site:reddit.com"
exa search "[产品类别] frustrating"
```

在报告的「覆盖平台列表」中，降级平台需标注：
```
Reddit：⚠️ 使用 Exa 全网搜索替代（直接访问未配置），结果质量低于直接访问
```

---

## 证据质量分级（来源周全性）

| 等级 | 条件 | 处理方式 |
|------|------|---------|
| **高** | 直接引用原话 + **可访问 URL** + 有点赞/互动数据 | 可计入评分维度证据 |
| **中** | 有来源平台，内容转述但逻辑清晰（或 URL 需登录）| 可作为辅助证据 |
| **低** | 仅有结论，无原始来源；或 URL 无法访问 | 标注「待验证」，不计入评分 |

**强制规则**：
- 高可信度条目必须附可公开访问的 URL（付费墙 / 需登录的标注 `[需登录]`，降为中）
- 不得引用无法回溯到真实来源的内容作为高可信度证据
- 标注各条证据的大致时间（如「2025 年 Q4 Reddit 帖子」）

---

## 搜索覆盖目标

每次执行 Step 2，目标：
- 覆盖全部 **7 个平台**（Reddit、X、小红书、App Store、Google Play、GitHub、Hacker News；未配置的标注降级原因）
- 高 + 中可信度合计 ≥ **15 条**
- 四种情绪类型（痛苦 / 妥协 / 期望 / 付费）各至少 **2 条**
- 至少 **1 条**来自 App Store 或 Google Play 的真实评论（两个商店均须执行搜索，不可只搜一个）
- 开发者工具 / 开源类 idea：至少 **1 条**来自 GitHub Issues 或 Discussions
- 至少 **5 个**不同平台有覆盖

未达到目标的维度，在报告中标注「证据不足，建议补充调研」。
