# Pain-Driven Search Framework · 搜索策略

## 核心原则

不搜话题，搜情绪。「productivity app」找到的是评测文章；「I hate my task manager because」找到的是真实用户痛点。目标是找到用户在没有人付钱让他们说好话时的真实声音。

**搜索词质量判断标准**：好的搜索词触发的结果情绪是「愤怒 > 失望 > 轻微不满」，而不是「这个产品不错」。

---

## 用户画像区域判断与平台选择

在开始搜索前，**必须先根据 Lean Hypothesis 中的目标用户判断平台范围**，避免在无关平台上浪费时间。

### 区域判断信号

| 信号类型 | 国内 🇨🇳 | 海外 🌐 | 全球 🌐🇨🇳 |
|---------|--------|--------|----------|
| 目标用户描述 | 明确提到中国用户、国内市场 | 明确提到海外、英语市场 | 「全球」「多语言」「不限地区」 |
| 竞品语言 | 竞品以中文为主 | 竞品以英文为主 | 中英文竞品均有 |
| 付费场景 | 微信支付、支付宝 | 信用卡、PayPal | 均有 |
| 内容场景 | 微博、微信、抖音 | Twitter、Instagram | 均有 |
| idea 语言 | 描述中以中文产品名/场景为主 | 描述中以英文产品名/场景为主 | 混合 |

### 平台选择矩阵

| 平台 | 🇨🇳 国内 | 🌐 海外 | 🌐🇨🇳 全球 | 技术向加权 |
|------|:-------:|:------:|:--------:|:--------:|
| Reddit | ❌ 跳过 | ✅ 必须 | ✅ 必须 | ✅ 优先 |
| X/Twitter | ❌ 跳过 | ✅ 必须 | ✅ 必须 | — |
| 小红书 | ✅ 必须 | ❌ 跳过 | ✅ 必须 | — |
| App Store (us) | ❌ 跳过 | ✅ 必须 | ✅ 必须 | — |
| App Store (cn) | ✅ 必须 | ❌ 跳过 | ✅ 必须 | — |
| Google Play | ❌ 跳过 | ✅ 必须 | ✅ 必须 | — |
| GitHub | ✅ 建议 | ✅ 必须 | ✅ 必须 | ✅ 必须 |
| Hacker News | ❌ 跳过 | ✅ 必须 | ✅ 必须 | ✅ 优先 |
| YouTube | ❌ 跳过 | ✅ 必须 | ✅ 必须 | — |
| 哔哩哔哩 | ✅ 必须 | ❌ 跳过 | ✅ 必须 | — |

> **注意**：❌ 跳过的平台需在报告中标注「已跳过（原因：目标用户为[区域]）」，不算缺失平台。

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
**降级**：Exa 全网搜索 `exa search "site:reddit.com query after:2024-12"`
**时间窗口**：优先最近 **6 个月**内的帖子；搜索时加时间过滤 `after:[6个月前日期]`

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
**降级**：Exa 全网搜索 `exa search "site:x.com query after:2024-12"`
**时间窗口**：优先最近 **6 个月**内；Twitter 搜索可加 `since:YYYY-MM-DD` 过滤

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

### YouTube（海外/全球 idea 执行，🌐）

**用户表达特点**：评论区是用户真实反应的高密度来源，尤其适合产品评测视频、「X vs Y」对比视频、「我为什么不再用 X」类视频；用户会在评论区直接表达痛点、推荐替代品、询问功能。一个热门视频的评论区可以提供数十条高价值用户声音。

**访问方式**：通过 Jina Reader 读取视频页面（含部分评论）
```bash
# 第一步：用 Exa 找到相关视频
exa search "youtube [竞品名] review problems" --num-results 5
exa search "youtube why I stopped using [竞品名]" --num-results 5
exa search "youtube best [产品类别] 2024" --num-results 5

# 第二步：用 Jina Reader 读取视频页面（含评论区）
curl "https://r.jina.ai/https://www.youtube.com/watch?v=[VIDEO_ID]"

# 第三步：如需更多评论，搜索视频评论关键词
exa search "site:youtube.com [竞品名] comments" --num-results 10
```

**搜索策略**：
- 找评测/对比类视频：`[竞品名] review` / `[竞品名] vs [竞品名2]` / `best [产品类别]`
- 找离开类视频：`why I quit [竞品名]` / `[竞品名] is ruining` / `stopped using [竞品名]`
- 找教程类视频评论（用户常在教程下提问/抱怨）：`how to use [竞品名]` / `[竞品名] tutorial`

**时间窗口**：优先最近 **6 个月**内发布的视频；但对热门老视频（100万+播放），最近评论区也有价值
**重点提取**：
- 置顶评论 + 高赞评论（往往是共鸣痛点）
- 「有没有类似但…」类评论（需求信号）
- 「我从 X 换过来的，因为…」类评论（迁移信号）
- 「为什么不支持…」类评论（功能缺口）

**每个启用视频目标**：≥ 5 条有效评论；建议覆盖 3–5 个不同视频。

---

### 哔哩哔哩（国内/全球 idea 执行，🇨🇳）

**用户表达特点**：B站评论区真实度高，技术类/效率类用户活跃度强；「我来分享一下踩坑经历」类评论是痛点金矿；弹幕中也有即时情绪反应，适合技术产品、生产力工具、创作工具类 idea。

**访问方式**：通过 Jina Reader + B站搜索接口
```bash
# 第一步：用 Jina Reader 搜索 B站相关视频
curl "https://r.jina.ai/https://search.bilibili.com/all?keyword=[竞品名]踩坑&order=click"
curl "https://r.jina.ai/https://search.bilibili.com/all?keyword=[产品类别]推荐&order=pubdate"

# 第二步：读取视频详情页（含评论区）
curl "https://r.jina.ai/https://www.bilibili.com/video/[BV号]"

# 第三步：用 Exa 补充搜索
exa search "site:bilibili.com [竞品名] 吐槽" --num-results 5
exa search "site:bilibili.com [产品类别] 不好用" --num-results 5
```

**搜索策略**：
- 找踩坑/评测：`[竞品名] 踩坑` / `[竞品名] 测评` / `[竞品名] 好不好用`
- 找对比类视频：`[竞品名] vs [竞品名2]` / `[产品类别] 哪个好`
- 找教程类评论（用户会在教程下提问）：`[竞品名] 教程` / `[竞品名] 怎么用`
- 找需求帖：`[产品类别] 有没有` / `希望 [产品类别]`

**时间窗口**：优先最近 **6 个月**内发布的视频；按播放量排序筛选高关注视频
**重点提取**：
- 高赞评论（共鸣度指标）
- 「我从 X 换过来的」类评论（迁移信号）
- 「为什么不能…」「什么时候支持…」类评论（功能缺口）
- 有追问/回复的长评论（深度痛点）

**每个启用视频目标**：≥ 5 条有效评论；建议覆盖 3–5 个不同视频。

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

## 时效性要求

| 时间范围 | 权重 | 处理方式 |
|---------|------|---------|
| 最近 **6 个月** | 高权重（主力证据） | 优先收集，作为评分依据 |
| 6 个月–1 年 | 中权重（辅助证据） | 可引用，需在条目中标注时间，如「2024 Q3」|
| **超过 1 年** | 低权重（备用/背景） | 仅在找不到更新证据时使用，标注「较旧，仅供参考」|

**实操原则**：各平台搜索时，**优先使用时间过滤参数**（如 `after:2024-12` / `sort=new`），确保结果时效性。

---

## 搜索覆盖目标

每次执行 Step 2，目标：

**数量目标**：
- 高 + 中可信度合计 ≥ **100 条**
- 四种情绪类型（痛苦 / 妥协 / 期望 / 付费）各至少 **10 条**
- 每个**启用平台**至少 **5 条**有效证据

**来源目标**：
- 覆盖**所有已启用平台**（根据用户画像区域判断；跳过的平台标注跳过原因，不算缺失）
- 至少 **1 条**来自 App Store（按区域选 us 或 cn）的真实用户评论
- 海外/全球 idea：至少 **5 条**来自 YouTube 评论区
- 国内/全球 idea：至少 **5 条**来自哔哩哔哩评论区
- 开发者工具 / 开源类 idea：至少 **5 条**来自 GitHub Issues 或 Discussions
- 至少 **5 个**不同平台有覆盖（跳过的不计入，未启用平台无需强求）

**时效性目标**：
- ≥ **80%** 的主力证据来自最近 6 个月内
- 超过 1 年的证据占比 ≤ **10%**

**不足时的处理**：
- 当前平台搜索不足 → 扩大搜索词范围、增加搜索次数（每类关键词至少尝试 3 组变体）
- 扩展搜索后仍不足 100 条 → 在报告中标注「证据不足：共 X 条，建议补充调研以下平台：[列表]」
- 不得因「来不及」或「找不到」就降低证据数量要求

未达到目标的维度，在报告中标注「证据不足，建议补充调研」。
