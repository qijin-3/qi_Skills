---
name: idea-validator
description: >
  Idea 快速验证工具 - 通过结构化多步骤方法论帮助独立开发者在投入开发前验证产品想法。
  覆盖危险信号预筛 → 假设锁定 → 用户声音挖掘（动态平台选择，最多 9 平台）→ 竞品解构 → 综合评估的完整流程，最终输出可视化 HTML 报告 + 用户反馈留档文件。
  当用户说「验证这个 idea」「分析这个产品想法」「帮我做市场调研」「这个方向值得做吗」「我有个想法」「走赛道 A」「这个产品可行吗」，或者直接描述一个产品/创业想法时触发。
---

# Idea Validator · 产品化验证

独立开发者视角的产品化 idea 验证流程。全程自动推进，用户只在 3 个节点参与：Step 0 预筛问题回答（可选）、Step 1 JTBD 回答、Step 1 假设确认。

**输出文件统一存放至** `/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/`：
- `report.html`：可视化 HTML 报告
- `user-feedback.jsonl`：用户反馈数据（JSONL，可跨次调研追加复用）
- `feedback-meta.json`：调研元信息（区域/平台/统计）

---

## 0. 前置安装检查（首次使用时执行）

运行以下命令检查 Agent-Reach 是否已安装：

```bash
agent-reach doctor
```

**如果命令不存在**，告知用户并引导安装：

> Agent-Reach 未安装。需要它才能访问 Reddit / X / 小红书。复制以下内容发给我：
>
> `帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md`
>
> 安装完成后，可选配置 Reddit / X / 小红书登录态：告诉我「帮我配 Reddit」即可。

**如果已安装**，直接查看 doctor 输出，记录哪些平台已配置、哪些未配置，进入 Step 0。未配置的平台静默降级（Exa 全网搜索），不打断用户。

---

## 平台访问配置（Step 2 依赖）

| 平台 | 适用区域 | 需要配置？ |
|------|---------|-----------|
| Reddit / X / 小红书 | 🌐 海外 / 🇨🇳 国内 | 需 Agent-Reach 配置，未配时降级为 Exa 全网搜索 |
| App Store / Google Play | 🌐🇨🇳 通用 | 无需配置（Jina Reader + iTunes API） |
| GitHub / Hacker News | 🌐 技术向 | 无需配置（gh CLI + Algolia API） |
| YouTube / 哔哩哔哩 | 🌐 海外 / 🇨🇳 国内 | 无需配置（Jina Reader） |

> 各平台完整命令、降级策略、时间窗口 → `references/search-strategy.md`
> 实际执行哪些平台由 Step 1d 的**目标用户区域判断**决定

---

## 执行规则

- 每个 Step 开始前输出：`▶ Step X / 4 · 标题`
- 每个 Step 完成后输出关键发现摘要，**立即自动进入下一步**，不询问
- 唯一等待节点：Step 0 提问 / Step 1 JTBD 提问 / Step 1 假设确认

---

## Step 0 · 危险信号预筛（可选）

如果用户已描述 idea，主动提示：「我想先问你 4 个快速问题（约 5 分钟），判断这个方向是否值得完整调研。要跳过直接进入正式流程也可以。」

用户选择跳过 → 直接进入 Step 1。

**逐一提问，不要一次性列出：**

- **A 护城河**：「你有什么别人难以复制的组合优势？（技能 + 资源 + 经验的组合，不是单一优势）」
- **B 商业模式历史**：「这种商业模式在历史上成功过吗？类似项目大多失败的原因是什么？」
- **C 创始人适配**：「如果产品成功了，你每天主要做什么？这些事情你喜欢，且能通过系统或团队自动化吗？」
- **D 竞争格局**：「现在有多少人在尝试同样的事？你是第一次创业吗？」

| 红灯数 | 处理 |
|--------|------|
| 0–1 | 直接进入 Step 1，红灯记录供 D5 评分参考 |
| 2 | 提示风险后询问是否继续 |
| 3–4 | 输出预警；D5 自动扣 5 分基础分；仍可继续 |

**输出格式**：
```
✓ 危险信号预筛完成
A 护城河：🟢/🟡/🔴  B 商业模式：🟢/🟡/🔴
C 创始人适配：🟢/🟡/🔴  D 竞争格局：🟢/🟡/🔴
红灯数：X / 4
```

---

## Step 1 · 假设锁定

> 提问框架详见 `references/jtbd-questions.md`

**1a.** 判断 idea 类型（工具类 / 内容类 / 平台类 / 服务类），决定提问侧重。

**1b.** 从五类 JTBD 问题中选 3–5 个（不要全问）：

| 问题类型 | 适用场景 | 示例问法 |
|---------|---------|---------|
| 触发时刻 | 所有类型必问 | 「什么情况下你会开始找这个问题的解决方案？」|
| 现有替代方案 | 所有类型必问 | 「你现在怎么处理这个问题？用什么工具？」|
| 替代方案不满 | 工具类/服务类必问 | 「现有方案让你最不满意的是什么？」|
| 切换阻力 | 平台类/内容类重点问 | 「是什么让你没有换掉现在的方案？」|
| 付费参照 | 所有类型必问 | 「你现在为解决这个问题花了多少钱？」|

等待用户回答后，执行 1c。

**1c.** 构建 Lean Hypothesis（六个字段必须全部填写）：
```
我们相信：[具体用户群]
在 [触发场景] 下遇到 [具体问题，含严重程度]
他们现在用 [替代方案] 处理
但不满是因为 [根本原因]
我们的差异化解法是 [核心差异点，一句话]
验证成功的信号是 [可量化指标]
```

**1d.** 呈现假设 → 等用户确认或修正 → 锁定后输出摘要，**同时判断用户画像区域**，进入 Step 2：

```
✓ 假设已锁定
目标用户：___  触发场景：___  核心痛点：___
现有替代：___  差异化方向：___  验证信号：___

📍 用户画像区域判断：[🌐 海外 / 🇨🇳 国内 / 🌐🇨🇳 全球]
启用平台：[列出将执行的平台列表]
跳过平台：[列出跳过的平台及原因]
```

**区域判断规则**（从目标用户描述、竞品语言、使用场景中推断）：

- 🇨🇳 国内：启用 小红书 / App Store(cn) / 哔哩哔哩 / GitHub；跳过 Reddit / X / Google Play / HN / YouTube
- 🌐 海外：启用 Reddit / X / App Store(us) / Google Play / GitHub / HN / YouTube；跳过 小红书 / 哔哩哔哩  
- 🌐🇨🇳 全球：启用全部 9 个平台，搜索词需中英双语
- 技术开发者向（任何区域）：额外确保 GitHub + HN 已启用

> 详细判断信号和平台矩阵 → `references/search-strategy.md`「用户画像区域判断与平台选择」

---

## Step 2 · 用户声音挖掘

> 搜索词生成规则、各平台完整命令、降级策略见 `references/search-strategy.md`

**2a. 生成搜索词矩阵**（根据区域判断生成对应语言的搜索词）：

| 类型 | 目的 | 模板示例 |
|------|------|---------|
| 痛苦词 | 验证痛点强度 | `[竞品名] frustrating / hate / broken` |
| 妥协词 | 找 workaround | `switched from [竞品] / [类别] workaround` |
| 期望词 | 找未被满足需求 | `wish [产品类别] could / feature request` |
| 付费词 | 验证付费意愿 | `worth paying for / [竞品] too expensive` |

**2b. 定向平台搜索**（仅执行 Step 1d 判断出的**启用平台**，跳过的平台在报告中标注原因）：

- **Reddit** → 情绪帖、迁移帖、求推荐讨论（🌐 海外/全球）
- **X/Twitter** → 实时抱怨、切换宣告、求推荐（🌐 海外/全球）
- **小红书** → 避坑帖、推荐帖评论区反对意见（🇨🇳 国内/全球）
- **App Store** → 两步法：iTunes API 查 App ID → Jina 读评论页；提取 1–2 星与功能缺失抱怨（🌐🇨🇳 通用，按区域选 us/cn）
- **Google Play** → 两步法：搜索页提取 `id=com.xxx` 包名 → Jina/curl 读详情页评论；提取 1–2 星与功能缺失抱怨（🌐 海外/全球）
- **GitHub** → `gh search issues` 搜痛点/功能请求；`gh search repos` 找开源竞品；对已知竞品仓库读 Issues/Discussions（技术向 idea 必须执行）
- **Hacker News** → 搜 `Ask HN: What do you use for X`、竞品 Show HN 评论区质疑（🌐 海外技术向）
- **YouTube** → 用 Jina Reader 抓取相关视频评论区，提取痛点与需求（🌐 海外/全球）
- **哔哩哔哩** → 搜索相关视频评论区，提取中文用户真实声音（🇨🇳 国内/全球）

**⏱️ 时效性要求**：所有证据**优先采集最近 6 个月**内的内容；超过 6 个月的内容降低权重（可引用但需注明时间，且不计入主力证据）；超过 1 年的内容仅在无其他证据时备用。

**2c. 构建结构化用户声音表**（≥ **100** 条高+中可信度；四种情绪类型各≥ 10 条；每个启用平台至少提供 **5 条**；开发者工具类 idea 需含 ≥ 5 条 GitHub 来源）：

| 平台 | 原始引用（附可访问 URL） | 中文翻译 | 情绪类型 | 可信度 | 时间 | 关联假设维度 |
|------|----------------------|---------|---------|-------|------|------------|

**翻译规则**：每条声音必须同时保存原文和中文译文。
- `content`：保留原始语言原文，不改写
- `content_zh`：`language` 为 `zh` 时与 `content` 相同；`en` / `other` 时填写准确中文翻译
- HTML 报告声音表：原文与 `content_zh` 分行展示（见 `references/html-report.md`）

> 若单次搜索凑不够 100 条，应扩大搜索词范围、增加搜索次数，而不是降低要求。若最终仍不足 100 条，在报告中明确标注「证据不足：共 X 条，建议补充调研」。

**2d. 结论摘要**（四个维度全部填写，不得省略任何一项）：
- **验证了假设的**：哪些证据支持了哪个字段（引用条数和平台）
- **挑战了假设的**：哪些证据与假设不符（**不得省略**）
- **未覆盖的**：哪些假设维度没找到证据，标注「证据不足」
- **意外发现**：原假设没有考虑到的需求信号

**2e. 用户反馈留档**（Step 2 完成后立即保存）：

> 字段定义、枚举值、分析命令 → `references/feedback-schema.md`

保存两个文件至 `/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/`：

**① `user-feedback.jsonl`**（每条声音一行，追加写入）：
```bash
# 每条记录格式（字段说明见 feedback-schema.md）
{"id":"reddit-0001","idea_slug":"<slug>","idea_name":"<name>","session_date":"YYYY-MM-DD","source_platform":"reddit","source_url":"<url>","source_type":"comment","source_region":"global","content":"<原文>","content_zh":"<中文翻译>","language":"en","search_query":"<搜索词>","sentiment_type":"pain","credibility":"high","hypothesis_dimension":"pain_point","published_at":"YYYY-MM-DD","is_recent":true,"competitors_mentioned":["<竞品>"],"engagement":{"upvotes":89,"comments":14,"views":null}}
```
若文件已存在（历史调研），直接追加；不要覆盖。

**② `feedback-meta.json`**（调研元信息，每次覆盖写入）：
```json
{
  "idea_slug": "<slug>",
  "idea_name": "<name>",
  "sessions": [{
    "session_date": "YYYY-MM-DD",
    "target_region": "global",
    "enabled_platforms": ["reddit","twitter","..."],
    "skipped_platforms": [{"platform":"xiaohongshu","reason":"目标用户为海外用户"}],
    "total_entries": 103,
    "high_credibility": 58,
    "medium_credibility": 45,
    "entries_recent_6m": 91
  }]
}
```

---

## Step 3 · 竞品解构

> 竞品定位矩阵方法、空白区判断逻辑见 `references/competitor-analysis.md`

**3a.** 从 Step 2 已出现的产品名开始，补充搜索 `best [类别] tools` / `[类别] alternatives` / `[类别] indie`。确定 3–6 个主要竞品（< 3 个时标注覆盖不足）。

**3b.** 对每个竞品收集：定价、核心定位、目标用户、用户高频抱怨（App Store/G2）、社区切换原因。

**3c.** 动态选择两个最能区分竞品的坐标轴，绘制定位矩阵，识别：竞争最激烈象限、明显空白象限、idea 潜在落点。

**3d.** 空白区有效性判断：必须同时满足「无成熟竞品」+「有 Step 2 用户声音支持」，二者缺一不算有效空白。

```
✓ 竞品解构完成
主要竞品：___  竞争最密集区域：___
有效空白：___（或「未识别」）  差异化切入建议：___
```

---

## Step 4 · 综合评估 + HTML 报告

> 评分区间、证据标准、防乐观偏差规则见 `references/scoring-rubric.md`
> HTML 视觉规范见 `references/html-report.md`

**4a. 5 维打分**（先列证据，再给分；< 3 条独立来源 → 自动封顶 60 分）：

| 维度 | 满分 | 核心问题 |
|------|------|---------|
| D1 痛点锐度 | 20 | 是「真的很痛（3–4 级）」还是「忍着用（1–2 级）」？|
| D2 利基可触达性 | 20 | 不投广告，能有机找到前 100 个用户吗？|
| D3 竞争空白 | 20 | 是否存在「大公司不屑、小团队没做好」的有效空白？|
| D4 付费意愿信号 | 20 | 有没有人已经在为这个问题花钱？|
| D5 MVP 可验证性 | 20 | 4 周内能低成本验证核心假设吗？|

| 总分 | Action |
|------|--------|
| ≥ 80 | `BUILD` |
| 60–79 | `FAST VALIDATE` |
| 40–59 | `PIVOT OR WAIT` |
| < 40 | `GRAVEYARD` |

**4b. 输出单文件 HTML 报告**：读取 `assets/report-template.html`，按 `references/html-report.md` 的说明逐步替换全部占位符，不要从零写 HTML：
- Tab 1 总览：Action Badge + 5 维雷达图 + 总分 + 机会点 + 风险 + MVP 路径
- Tab 2 用户声音：结论摘要 + 可筛选声音表（含时间列、平台覆盖统计）
- Tab 3 竞品分析：定位矩阵（SVG）+ 竞品数据表 + 有效空白说明
- Tab 4 评估详情：每维度证据列表 + 得分理由 + 不足警告
- Tab 5 Lean Canvas：九格 Canvas，无证据格子标注「待验证」

**保存路径**：`/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/report.html`

- `<idea-slug>` 从 idea 名称生成（英文小写 + 连字符，如 `ai-writing-tool`）
- 若目录不存在则自动创建：`mkdir -p "/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>"`
- 若该目录已存在 `user-feedback.jsonl`（历史调研留档），读取其 `session_date` 列表，在报告 Tab 2 中注明「已有 X 次历史调研，本次新增 Y 条」

---

## 禁止事项

**证据质量**
- 不得引用无法回溯到真实来源的用户声音（无可访问 URL → 降为中/低可信度）
- 不得在证据 < 3 条时突破封顶规则给高分
- 不得因用户语气自信就给高分

**分析质量**
- 不得写通用结论（「用户希望产品更好用」无价值）；结论必须含具体产品名/功能缺失/场景
- 不得省略挑战假设的证据；2d 四个维度必须全部填写
- 不得只选支持性证据；矛盾证据必须显式列出
- 不得编造用户引用或竞品数据

**流程**
- 不得跳过 Step 1 的用户确认节点
- 不得输出 Markdown 格式的最终报告（必须是 HTML）
- 不得在 Step 2–3 中途停下来询问用户
- 不得对明显面向海外用户的 idea 执行小红书/哔哩哔哩搜索（无效数据污染结论）
- 不得对明显面向国内用户的 idea 执行 Reddit/HN/Google Play 搜索（同上）
- 不得以「证据不够」为由跳过任何**启用平台**；证据不足应扩大搜索词后重试
- 不得引用超过 1 年的内容作为主力证据（时效性失效）

---

## 输出前自查

- [ ] Agent-Reach 状态已检查，降级平台已标注
- [ ] Step 0 红灯记录已传递到 D5 评分
- [ ] Lean Hypothesis 六个字段全部填写，验证信号含可量化指标
- [ ] **用户画像区域已判断**，启用/跳过平台已在摘要中列出并说明原因
- [ ] 所有启用平台均已执行搜索；每个启用平台至少 5 条证据
- [ ] **时效性**：证据以最近 6 个月内为主；超期内容已标注时间并降低权重
- [ ] 用户声音表：≥ 100 条高+中可信度；高可信度条目全部附可访问 URL；含时间列；每条含 `content` + `content_zh`
- [ ] **user-feedback.jsonl 和 feedback-meta.json 已保存**至 `/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/`（jsonl 追加写入，不覆盖历史数据；每条记录含 `content_zh`）
- [ ] 2d 结论四个维度全部填写，包括「挑战了假设的」
- [ ] 竞品 3–6 个；空白区结论有双条件验证
- [ ] 每个评分维度先列证据再给分，证据不足维度已封顶并标注
- [ ] **HTML 报告已保存**至 `/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/report.html`，包含全部 5 个 Tab，离线可打开；平台覆盖含 YouTube / 哔哩哔哩计数；声音表含原文 + 中文翻译
- [ ] MVP 路径每步包含可量化成功信号
