# HTML 报告规范 · idea-validator

## 核心原则

**始终从 `assets/report-template.html` 开始，不要从零写 HTML。**

模板已内置：Swiss International 视觉系统、5 Tab 结构、全部组件样式、Tab/筛选 JS。
你的工作只是替换占位符并插入数据。

---

## 使用步骤

### 1. 复制模板

将 `assets/report-template.html` 内容作为输出 HTML 的基础。

### 2. 替换全局占位符

| 占位符 | 替换内容 |
|--------|---------|
| `{{IDEA_TITLE}}` | Idea 标题（简短，< 30 字）|
| `{{GENERATED_DATE}}` | 生成时间，如 `2026-06-22` |
| `{{HYPOTHESIS_ONE_LINER}}` | 核心假设一句话（30–60 字）|
| `{{ACTION_CLASS}}` | `build` / `fast` / `pivot` / `grave` |
| `{{ACTION_LABEL}}` | `BUILD` / `FAST VALIDATE` / `PIVOT OR WAIT` / `GRAVEYARD` |
| `{{TOTAL_SCORE}}` | 总分数字 |

### 3. 填入评分数据

| 占位符 | 说明 |
|--------|------|
| `{{D1}}` ~ `{{D5}}` | 各维度分数（整数）|
| `{{D1_PCT}}` ~ `{{D5_PCT}}` | 百分比 = 分数 / 20 × 100，填入 `style="width:X%"` |

**证据不足警告**：如果某维度分数因证据不足被封顶，取消 Tab 4 中对应 `.evidence-warning` 块的注释，并填入补充调研建议。

### 4. 填入 Tab 1 · 总览

| 占位符 | 内容 |
|--------|------|
| `{{BIGGEST_OPPORTUNITY}}` | 最大机会点（1–2 句，引用平台名和条数）|
| `{{BIGGEST_RISK}}` | 最大风险（1 句，最影响成功的不确定因素）|
| `{{MVP_STEP1/2/3_ACTION}}` | MVP 3 步行动 |
| `{{MVP_STEP1/2/3_SIGNAL}}` | 各步骤的可量化成功信号 |
| `{{NEXT_ACTION_TEXT}}` | 本周立即可执行的 1 个具体行动 |
| `{{NEXT_ACTION_TIME}}` | 预计耗时，如「2 小时」|

### 5. 填入 Tab 2 · 用户声音

**结论摘要**（4 个格子，全部必填）：

| 占位符 | 说明 |
|--------|------|
| `{{VOICE_VERIFIED}}` | 验证了假设的证据摘要 |
| `{{VOICE_CHALLENGED}}` | 挑战了假设的证据摘要（**不得留空**）|
| `{{VOICE_GAPS}}` | 证据未覆盖的假设维度 |
| `{{VOICE_SURPRISES}}` | 意外发现的需求信号 |

**声音表**：将 `{{VOICE_ROWS}}` 注释替换为实际 `<tr>` 行，每行模板：

```html
<tr data-emotion="pain">  <!-- pain | workaround | wish | pay -->
  <td>Reddit</td>
  <td>
    「原始引用原话」—
    <a href="https://..." style="color:var(--grey-3);font-size:11px;">来源链接</a>
  </td>
  <td><span class="emotion-tag">抱怨</span></td>
  <td><span class="trust-badge trust-high">高</span></td>  <!-- trust-high | trust-mid | trust-low -->
  <td>核心痛点</td>
</tr>
```

**平台覆盖**：替换 `{{REDDIT_COUNT}}` 等各平台计数（含 `{{GITHUB_COUNT}}`、`{{GPLAY_COUNT}}`）。
降级平台在对应 `.platform-cell` 上添加 class `platform-degraded`，status 写「⚠ Exa 替代，可信度降低」。

### 6. 填入 Tab 3 · 竞品分析

**定位矩阵 SVG**：
- 将 `{{AXIS_X_LEFT}}` / `{{AXIS_X_RIGHT}}` / `{{AXIS_Y_TOP}}` / `{{AXIS_Y_BOTTOM}}` 替换为实际坐标轴标签
- 将 `{{MATRIX_DOTS}}` 注释替换为实际圆点：

```html
<!-- 竞品落点 -->
<circle cx="180" cy="130" r="6" fill="#0a0a0a"/>
<text x="190" y="127" font-family="IBM Plex Mono,monospace" font-size="11" fill="#555553">竞品名</text>

<!-- idea 落点（空心圆区分） -->
<circle cx="420" cy="90" r="9" fill="none" stroke="#0a0a0a" stroke-width="2"/>
<text x="433" y="87" font-family="IBM Plex Mono,monospace" font-size="11" fill="#0a0a0a">← Your idea</text>
```

- 替换 `{{MATRIX_AXIS_REASON}}` 为坐标轴选择理由

**竞品表**：将 `{{COMPETITOR_ROWS}}` 替换为实际竞品行（每行含产品名、定价、定位、目标用户、Top 3 抱怨）。

**有效空白**：替换 `{{BLANK_SPACE_TEXT}}`：
- 有空白：说明象限 + 矩阵证据 + Step 2 用户声音条数和平台
- 无空白：写「未识别到有效空白。[原因]」

### 7. 填入 Tab 4 · 评估详情

对每个维度（D1–D5）：
- 将 `{{D1_EVIDENCE}}` 注释替换为实际证据条目（每条包含平台、引用摘要、可信度）
- 替换 `{{D1_REASON}}` 为得分理由（先证据后结论）

### 8. 填入 Tab 5 · Lean Canvas

| 占位符 | 对应格子 |
|--------|---------|
| `{{CANVAS_PROBLEM}}` | 用户痛点（来自 Step 1）|
| `{{CANVAS_SOLUTION}}` | 解决方案（来自假设）|
| `{{CANVAS_UVP}}` | 独特价值主张（来自差异化方向）|
| `{{CANVAS_ADVANTAGE}}` | 竞争优势（来自 Step 0 护城河）|
| `{{CANVAS_SEGMENTS}}` | 目标用户（来自假设）|
| `{{CANVAS_METRICS}}` | 关键指标（来自验证信号）|
| `{{CANVAS_CHANNELS}}` | 获客渠道（来自 Step 2 平台分布）|
| `{{CANVAS_COST}}` | 成本结构（时间/开发/获客）|
| `{{CANVAS_REVENUE}}` | 收入来源（来自 Step 3 竞品定价参照）|

无证据支撑的格子：在对应 `.canvas-cell` 上添加 class `unverified`，内容写「待验证」。

---

## 最终检查

- [ ] 所有 `{{...}}` 占位符已全部替换（无遗漏）
- [ ] 5 个 Tab 均有内容
- [ ] Tab 2 中「挑战了假设的」格子不为空
- [ ] 证据不足的维度已显示 `.evidence-warning` 块
- [ ] 降级平台已标注
- [ ] CSS / JS 全部内联，无外部依赖，离线可打开
