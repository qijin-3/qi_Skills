# HTML 灵感卡片产出规范（Phase 4 必读）

Phase 4 的**最终交付物**是一张可离线打开的 HTML 灵感卡片，不是 Markdown 概念卡。

视觉体系参考 `skills/design/guizang-social-card-skill-main` 的 **Editorial Magazine** 模式：衬线标题、纸质感、细规则、issue strip、克制的排版层级。**不要从零写 HTML**——必须基于 skill 内置模板填充。

---

## 一、模板与样例（禁止从零写）

| 文件 | 用途 |
|------|------|
| `assets/concept-card-template.html` | **唯一合法起点**。读取全文，替换 `[[占位符]]`，写出最终 HTML |
| `assets/concept-card-sample.html` | 填好后的质量参照（过劳报警器）。不确定排版时长什么样，先读这个 |

**硬性规则**：
- 不得删除模板中的 CSS 结构（`:root` 主题 token、`.card`、`.grain`、`.section`、`.tab-nav` 等）
- 不得引入 WebGL / **外部** JS 依赖（模板内置的 Tab 切换脚本除外，保证离线稳定）
- 只替换占位符内容，可微调 `data-theme`，不改 DOM 骨架（含两个 Tab 面板结构）
- `[[NAME_TAGS]]`、`[[HOOK_ITEMS]]`、`[[IDEA_LOG_ITEMS]]`、`[[USER_REVISION_ITEMS]]` 是 HTML 片段，不是纯文本

---

## 二、占位符清单

| 占位符 | 填入内容 |
|--------|---------|
| `[[THEME]]` | 主题名（见下表） |
| `[[DATE]]` | `YYYY.MM.DD` |
| `[[CONCEPT_NAME]]` | 选定的主产品名（中文优先） |
| `[[CONCEPT_NAME_EN]]` | 英文名或副标题；无则留空或写 `—` |
| `[[CONCEPT_SLUG]]` | 文件名 slug（不含 `.html`） |
| `[[ONE_LINER]]` | 一句话定义：「一个让你___的___」 |
| `[[EMOTION_KERNEL]]` | Phase 1 确认的情绪内核 |
| `[[THINKING_METHOD]]` | 该方向的思维方法 + 一句话说明 |
| `[[AXIS_FORM]]` | 感知形态（A 轴） |
| `[[AXIS_POWER]]` | 传播动力（B 轴） |
| `[[NAME_TAGS]]` | 2–3 个 `<span class="name-tag">`；首选加 `primary` class |
| `[[EMOTION_MOMENT]]` | 核心情绪时刻 |
| `[[INTERACTION_METAPHOR]]` | 「动作 = 情绪意义」动词等式 |
| `[[VISUAL_DIRECTION]]` | 色彩 + 动态 + 氛围三要素 |
| `[[HOOK_ITEMS]]` | 2–3 个 `<li>...</li>` |
| `[[VIBE_CODING_PROMPT]]` | 完整 vibe coding 提示词（`&` 转 `&amp;`） |
| `[[IDEA_COUNT]]` | Phase 3 发散方向总数（数字，如 `6`） |
| `[[IDEA_LOG_ITEMS]]` | **发散记录 Tab**：Phase 3 全部方向的 HTML 卡片列表（见下） |
| `[[USER_REVISION_ITEMS]]` | **发散记录 Tab**：用户在 Phase 1–3 中调整/补充的新 idea；无则填空状态 `<p class="idea-log-empty">本次会话无用户调整记录。</p>` |

### `[[IDEA_LOG_ITEMS]]` 单条结构

每个 Phase 3 方向一条 `<article class="idea-log-item">`。用户最终选中的方向加 `selected` class 和 `<span class="idea-status selected">已选中</span>`，其余为 `<span class="idea-status">备选</span>`。

```html
<article class="idea-log-item selected">
  <div class="idea-log-head">
    <h3 class="idea-log-name">过劳报警器</h3>
    <span class="idea-status selected">已选中</span>
  </div>
  <div class="idea-log-meta">
    <span class="idea-method">自由漂移</span>
    <span>身体型 × 压不住的笑</span>
  </div>
  <p class="idea-log-field"><strong>交互隐喻</strong>持续高效工作 = 触发警报，被强制摸鱼</p>
  <p class="idea-log-field"><strong>情绪时刻</strong>正干得起劲，机器突然像抓现行一样……</p>
</article>
```

字段来源：Phase 3 每个方向的【方向名称】、思维方法、双轴定位、交互隐喻、情绪时刻。视觉意象可省略以控制篇幅。

### `[[USER_REVISION_ITEMS]]` 单条结构

用户在对话中修正情绪内核、改写某个方向、或提出新变体时记录。加 `revised` class：

```html
<article class="idea-log-item revised">
  <div class="idea-log-head">
    <h3 class="idea-log-name">报警语气再狠一点</h3>
    <span class="idea-status revised">用户调整</span>
  </div>
  <p class="idea-log-field"><strong>调整说明</strong>用户希望警告文案更像系统蓝屏……</p>
  <p class="idea-log-field"><strong>新内容</strong>「检测到过劳，已为您强制休息」</p>
</article>
```

### `[[NAME_TAGS]]` 示例

```html
<span class="name-tag primary">过劳报警器</span>
<span class="name-tag">OverWork Alarm</span>
<span class="name-tag">太努力了 警告</span>
```

### `[[HOOK_ITEMS]]` 示例

```html
<li>全网第一个你越努力它越生气的 App</li>
<li>检测到过劳，已为您强制休息。</li>
```

---

## 三、主题选择（按情绪重量）

| 情绪重量 | 推荐 `data-theme` | 气质 |
|---------|-------------------|------|
| 沉 / 克制 / 隐忍 | `indigo-porcelain` `forest-ink` `midnight-ink` | 安静、有重量 |
| 中 / 温暖 / 被代言 | `ink-classic` | 默认杂志感 |
| 轻 / 荒诞 / 反卷 | `kraft-paper` `dune` | 暖、有点胡闹 |
| 反差 / 警示 / 工业荒诞 | `kraft-paper`（默认）或保留警示色在文案里 | 如过劳报警器 sample |

不设限时默认 `ink-classic`。轻的 idea **禁止**用 `midnight-ink`（太沉）。

---

## 四、保存路径与文件命名

**固定输出目录**：

```
/Users/jin/SynologyDrive/Working/Ideas/💥 Brainstorm/
```

**写入前执行**（目录不存在则创建）：

```bash
mkdir -p "/Users/jin/SynologyDrive/Working/Ideas/💥 Brainstorm"
```

**文件命名**：按**选定概念的主产品名**命名，扩展名 `.html`。

| 产品名 | 文件名 |
|--------|--------|
| 过劳报警器 | `过劳报警器.html` |
| 我很好生成器 | `我很好生成器.html` |
| Eternal Sunset | `eternal-sunset.html` |

**Slug 规则**：
1. 中文产品名 → 直接用中文（macOS 支持）
2. 纯英文 → 小写 + 连字符
3. 去掉 `/ \ : * ? " < > |` 等非法字符
4. 用户选了 2 张概念卡 → 各写一个 HTML，不合并

**完成后告知用户**：

```
灵感卡片已保存：
/Users/jin/SynologyDrive/Working/Ideas/💥 Brainstorm/[[CONCEPT_SLUG]].html
用浏览器打开即可查看。
```

---

## 五、产出流程（Phase 4 执行顺序）

1. 在对话中简要确认选中的方向（可 1–2 句摘要）
2. **Read** `assets/concept-card-template.html`
3. 对照 `references/concept-card-spec.md` 填齐六个字段
4. 按上表替换所有 `[[占位符]]`，**含发散记录 Tab**：
   - `[[IDEA_LOG_ITEMS]]`：回填 Phase 3 全部 6–8 个方向（选中项标记 `selected`）
   - `[[USER_REVISION_ITEMS]]`：回填会话中用户修正/补充的 idea（Phase 1 情绪内核修正、Phase 3 方向改写、用户自发新方向等均记录）
   - `[[IDEA_COUNT]]`：与 `IDEA_LOG_ITEMS` 条数一致
5. **Write** 到 Brainstorm 目录（不是 workspace 内）
6. 对话结尾给出保存路径，提示用户切换到「发散记录」Tab 可查看完整素材库；**禁止**只输出 Markdown 概念卡而不写文件

若用户一次选了 2 个方向，重复 2–5 步，各生成一张 HTML。

---

## 六、质量自检（HTML 专用）

- [ ] 基于 `concept-card-template.html`，未从零写 HTML
- [ ] 所有 `[[占位符]]` 已替换，无残留 `[[`
- [ ] **发散记录 Tab**：`IDEA_LOG_ITEMS` 含 Phase 3 全部方向；选中项已标记；`USER_REVISION_ITEMS` 已回填或为空状态
- [ ] `data-theme` 与情绪重量匹配，轻的未用 midnight-ink
- [ ] 六字段内容齐全；候选名 2–3 个；传播钩子 2–3 条
- [ ] vibe coding 块中 HTML 特殊字符已转义
- [ ] 文件已写入 `.../Ideas/💥 Brainstorm/` 且按概念命名
- [ ] 语言风格与情绪内核重量一致，无升华
