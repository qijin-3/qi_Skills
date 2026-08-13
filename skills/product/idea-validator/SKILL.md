---
name: idea-validator
description: >
  面向独立开发者 / 早期创业者，验证「SaaS / App / 独立软件产品」想法是否值得继续投入。
  基于公开网络用户讨论与竞品信息，输出固定结构的 HTML 验证报告。
  适用：写代码前确认软件产品痛点是否真实、竞品空白是否存在。
  触发示例：「验证这个产品idea」「这个独立软件产品方向值得做吗」。
---

# Idea Validator · 软件产品想法验证

独立开发者视角的 **SaaS / App / 独立软件产品** idea 验证。全程自动推进；用户参与节点：Step 0（可选）、Step 1 JTBD + 假设确认、Step 5 PRD（可选）。

**范围：** 只验证软件产品类想法并产出结构化报告；不生成文案/营销内容，不提供医疗/法律/金融建议，不编造用户引用或竞品数据。

**输出目录** `$IDEA_DIR` = `/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/`  
`<idea-slug>`：英文小写 + 连字符；目录不存在则 `mkdir -p`。

| 文件 | 说明 |
|------|------|
| `report.html` | HTML 验证报告（必出） |
| `user-feedback.jsonl` | 用户声音留档（追加写入） |
| `feedback-meta.json` | 调研元信息 |
| `prd.md` | PRD（可选，用户确认后） |

---

## 渐进加载：何时读哪个文件

Skill 正文只保留流程与门槛。细节按需打开，避免一次塞满上下文。

| 时机 | 读取 |
|------|------|
| 进入 Step 0 | `references/prescreen.md` |
| 进入 Step 1 | `references/jtbd-questions.md` |
| Step 1d 判区域 | `references/search-strategy.md`「区域判断」 |
| 进入 Step 2 前 | `references/platform-access.md`（体检 + 降级；缺能力不中断） |
| Step 2 搜索 | `references/search-strategy.md`（先「搜索词」，再读各启用平台小节） |
| Step 2e 写留档 | `references/feedback-schema.md` |
| 进入 Step 3 | `references/competitor-analysis.md` |
| 进入 Step 4 打分 | `references/scoring-rubric.md` |
| Step 4 写 HTML | `assets/report-template.html` + `references/html-report.md` |
| 用户确认要 PRD | `references/prd-template-guide.md` → 再读 `references/prd-templates/<id>.md` |
| 交付前 | `references/delivery-checklist.md` |

`search-strategy.md` 较长：只读当前需要的章节，不要整文件通读。

---

## 执行规则

- 每步开始：`▶ Step X / 5 · 标题`
- 每步结束后输出关键发现，**立刻进入下一步**（除等待节点外不问）
- **等待节点**：Step 0 提问 / Step 1 JTBD / Step 1 假设确认 / Step 5 PRD 确认
- Step 4 完成后必须询问是否整理 PRD

---

## Step 0 · 危险信号预筛（可选）

读取并执行 `references/prescreen.md`。跳过则直接 Step 1。红灯数写入后续 D5。

---

## Step 1 · 假设锁定

读取 `references/jtbd-questions.md`。

**1a.** 判断 idea 类型（工具 / 内容 / 平台 / 服务），决定提问侧重。  
**1b.** 按该文件从五类 JTBD 中选 3–5 个提问（不要全问）。等用户答完再继续。

**1c.** 构建 Lean Hypothesis（六字段全填）：

```
我们相信：[具体用户群]
在 [触发场景] 下遇到 [具体问题，含严重程度]
他们现在用 [替代方案] 处理
但不满是因为 [根本原因]
我们的差异化解法是 [核心差异点，一句话]
验证成功的信号是 [可量化指标]
```

**1d.** 呈现假设 → **等用户确认** → 锁定后判断区域并列出启用/跳过平台。

读取 `references/search-strategy.md`「用户画像区域判断与平台选择」执行判断；摘要格式：

```
✓ 假设已锁定
目标用户：___  触发场景：___  核心痛点：___
现有替代：___  差异化方向：___  验证信号：___

📍 用户画像区域判断：[🌐 海外 / 🇨🇳 国内 / 🌐🇨🇳 全球]
启用平台：[...]
跳过平台：[...及原因]
```

---

## Step 2 · 用户声音挖掘

先读 `references/platform-access.md`（确认直连/降级），再读 `references/search-strategy.md`：先「搜索词矩阵」，再按启用平台读对应小节与「时效性 / 覆盖目标」。

**门槛（不可降）：**

- 证据优先最近 **6 个月**；超 1 年仅备用
- ≥ **100** 条高+中可信度；四种情绪各 ≥ 10；每启用平台 ≥ **5**；开发者工具类 GitHub ≥ 5
- 凑不够 → 扩大搜索词重试，不降标准；仍不够则报告标注「证据不足：共 X 条」

**2c 声音表列：** 平台 | 原始引用(+URL) | 中文翻译 | 情绪 | 可信度 | 时间 | 关联假设维度  
每条保留 `content`（原文）+ `content_zh`（中文）。

**2d 结论四栏全填：** 验证了假设的 / 挑战了假设的（必填）/ 未覆盖的 / 意外发现

**2e 留档：** 读 `references/feedback-schema.md`，写入 `$IDEA_DIR`：
- `user-feedback.jsonl` — 追加，不覆盖历史
- `feedback-meta.json` — 本次会话元信息（可覆盖写当前 sessions 结构，按 schema）

---

## Step 3 · 竞品解构

读取 `references/competitor-analysis.md`。

**3a.** 从 Step 2 产品名扩展搜索，定 3–6 个主竞品（<3 标注覆盖不足）。  
**3b.** 收集：定价、定位、目标用户、高频抱怨、切换原因。  
**3c.** 选两轴绘定位矩阵，标激烈象限 / 空白象限 / idea 落点。  
**3d.** 有效空白 =「无成熟竞品」**且**「有 Step 2 声音支持」，缺一不算。

```
✓ 竞品解构完成
主要竞品：___  竞争最密集区域：___
有效空白：___（或「未识别」）  差异化切入建议：___
```

---

## Step 4 · 综合评估 + HTML 报告

读取 `references/scoring-rubric.md` 打分；写报告前读 `references/html-report.md`，并从 `assets/report-template.html` 替换占位符（不要从零写 HTML）。

**4a.** 先列证据再给分；独立来源 < 3 → 按 `scoring-rubric.md` 封顶。五维：D1 痛点锐度 / D2 利基可触达 / D3 竞争空白 / D4 付费意愿 / D5 MVP 可验证（各 20）。

| 总分 | Action |
|------|--------|
| ≥ 80 | `BUILD` |
| 60–79 | `FAST VALIDATE` |
| 40–59 | `PIVOT OR WAIT` |
| < 40 | `GRAVEYARD` |

**4b.** 五 Tab：总览 · 用户声音 · 竞品分析 · 评估详情 · Lean Canvas → `$IDEA_DIR/report.html`  
若已有历史 `user-feedback.jsonl`，Tab 2 注明「已有 X 次调研，本次新增 Y 条」。

**4c.** HTML 保存后**必须停下**询问是否整理 PRD：

```
▶ Step 5 / 5 · PRD（可选）
HTML 已保存。是否基于本次验证结果整理 Markdown PRD？
- 「要」→ Step 5
- 「不要」→ 结束并输出完成摘要
```

---

## Step 5 · PRD（可选）

读取 `references/prd-template-guide.md` 选模板并说明理由；再读对应 `references/prd-templates/<id>.md` 填充。  
只用本次报告已有数据，缺失标「待补充」，不编造。保存 `$IDEA_DIR/prd.md`。

```
✓ PRD 已生成
模板：[中文名]  路径：…/prd.md  说明：[一句话理由]
```

---

## 质量红线

这套流程的价值是在投入几个月前把坏消息说出来。破了下面几条，报告就只是自我安慰：

1. **证据可回溯** — 无 URL → 降可信度；独立来源不足 → 按 rubric 封顶；自信语气不加分  
2. **矛盾证据必写** — 2d「挑战了假设的」空着 = 把验证做成了确认  
3. **结论可落地** — 落到具体产品名 / 缺失功能 / 场景，禁止空泛「更好用」  
4. **只搜目标用户所在平台** — 区域错则信号污染；证据以 6 个月内为主  
5. **证据不足是结论不是借口** — 扩词重试；不够就写明条数；禁止编造  
6. **该停则停** — Step 1 / Step 5 必须等用户；Step 2–3 不要中途打断  

交付前读取并勾选 `references/delivery-checklist.md`。
