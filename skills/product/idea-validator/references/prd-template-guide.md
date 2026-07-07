# PRD 模板选择指南 · idea-validator

HTML 报告完成后，若用户选择生成 Markdown PRD，按本指南选择模板、映射验证数据、输出 `prd.md`。

**保存路径**：`/Users/jin/SynologyDrive/Working/Ideas/<idea-slug>/prd.md`

---

## 何时询问

Step 4 HTML 报告保存成功后，**必须停下来询问**：

> HTML 报告已保存至 `…/report.html`。
>
> 是否需要基于本次验证结果生成 **Markdown 格式的 PRD**？
> - 回复「要」/「生成 PRD」→ 自动选择最合适模板并生成
> - 回复「不要」/跳过 → 流程结束

用户未明确回应前，不得自动生成 PRD。

---

## 模板速览

| 模板 | 来源 | 篇幅 | 最适合场景 |
|------|------|------|-----------|
| **lenny-one-pager** | Lenny Rachitsky 个人一页纸 | 短（~1 页） | 独立开发者、首次把验证结论落成行动文档；BUILD / FAST VALIDATE |
| **adam-initiative** | Adam Thomas 倡议模板 | 短（严格 1 页） | 需要向合伙人/投资人说明投入产出；强调成功/失败/生存线 |
| **steve-morin-one-pager** | Steve Morin 1-Pager | 中（~2 页） | 技术向产品、有明确工程依赖；开发者工具、API、多端 |
| **asana-brief** | Asana 项目简报 | 中长 | 新产品的叙事驱动立项；JTBD 故事线强、需假设+愿景叙事 |
| **figma-prd** | Figma PRD | 中长 | 现有产品的新功能；设计流程重、需发布检查清单 |
| **kevin-yien-prd** | Kevin Yien PRD | 长 | 多角色团队、正式分阶段上线；BUILD 且需跨职能对齐 |

各模板完整结构见 `references/prd-templates/<template-id>.md`。

---

## 自动选择决策树

按**第一条命中**的规则选择模板（从上到下）：

```
1. 用户明确指定模板名？
   → 使用用户指定模板

2. Action = GRAVEYARD 或 PIVOT OR WAIT？
   → lenny-one-pager（轻量记录验证结论与 pivot 方向，不写完整立项）

3. idea 类型 = 工具类 且 目标用户含「开发者/工程师」？
   → steve-morin-one-pager

4. 用户提到「现有产品/已有 App/加功能/迭代」？
   → figma-prd

5. 用户提到「团队/合伙人/融资/向老板汇报」或 Step 0 非首次创业？
   → adam-initiative

6. Action = BUILD 且 总分 ≥ 80？
   → kevin-yien-prd

7. Action = BUILD 或 FAST VALIDATE，且 Lean Hypothesis 叙事丰富（触发场景+情绪细节完整）？
   → asana-brief

8. 默认（独立开发者、首次立项）
   → lenny-one-pager
```

选定后向用户说明：**「根据 [原因]，选用 [模板中文名] 模板。」** 若用户想换模板，尊重其选择。

---

## 数据映射（验证报告 → PRD 字段）

从本次验证流程提取内容，**不得编造**报告中没有的数据；缺失项标注「待补充」或「待验证」。

| PRD 常见字段 | 数据来源 |
|-------------|---------|
| 项目名称 / 标题 | idea 名称 |
| 问题陈述 | Lean Hypothesis「具体问题」+ Step 2「验证了假设的」|
| 目标用户 / 受众 | Lean Hypothesis「具体用户群」+ 区域判断 |
| 为什么现在做 | Step 2 用户声音条数 + 高可信度证据摘要 |
| 高层方案 / 做什么 | Lean Hypothesis「差异化解法」+ Tab 1 MVP 路径 |
| 成功标准 / 关键结果 | Lean Hypothesis「验证信号」+ D1–D5 高分维度证据 |
| 非目标 | Step 3 竞品密集区（明确不正面硬刚的方向）|
| 竞品 / 背景 | Step 3 竞品表 + 定位矩阵结论 |
| 风险 | Tab 1 最大风险 + Step 0 红灯 + 「挑战了假设的」|
| 假设 | Lean Hypothesis 全文（六个字段）|
| MVP / 实验计划 | Tab 1 MVP 三步 + Action 建议 |
| 时间线 | MVP 各步成功信号的时间预期（合理推断，标注为估算）|
| 用户叙事 | Step 2 典型用户引用 1–2 条（原文+译文）|
| 功能清单 | Tab 5 Lean Canvas「Solution」+「Key Metrics」拆解 |
| 发布检查 | 仅 kevin-yien / figma 模板：从 MVP 路径推导里程碑 |

**评分与 Action 写入方式**：
- lenny / adam / steve-morin：在「成功定义」或「Success/Survival」中引用总分与 Action
- asana：写入「假设」与「目标」
- figma / kevin-yien：写入「目标与成功」并附验证报告链接路径

---

## 生成规则

1. 读取 `references/prd-templates/<template-id>.md` 作为结构骨架
2. 用验证数据填充各节；保留模板中的引导性小标题
3. 文首添加元信息块：

```markdown
---
title: [项目名称] PRD
template: [template-id]
generated_from: idea-validator
validation_date: YYYY-MM-DD
action: BUILD | FAST VALIDATE | PIVOT OR WAIT | GRAVEYARD
total_score: NN
report: ../report.html
---
```

4. 文末添加：

```markdown
---
> 本 PRD 由 Idea Validator 验证报告自动生成。完整证据见同目录 `report.html` 与 `user-feedback.jsonl`。
```

5. 保存后告知用户路径，并一句话概括所选模板原因。

---

## 禁止事项

- 不得在用户未确认时生成 PRD
- 不得编造验证报告中不存在的用户引用或竞品数据
- GRAVEYARD 结论不得写成「强烈推荐立项」语气；应如实反映验证结论
- 不得输出 HTML 格式的 PRD（Markdown only）
