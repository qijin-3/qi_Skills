# 各板块写作规格

子 agent **只根据**对应 `raw/*.json` 写稿，禁止编造。24h 过滤与抓取失败已由脚本处理——写稿时如实反映空仓/失败即可，不必复述脚本逻辑。

## 共用

- 先结论后论据；日报 Tab 内不要源统计表；不要 `ul.evidence` 长列表。
- 结构：`.section-head` + `.news-row` 或 `.topic` + cite-badge。
- **有 `image` 时**：放在 `.news-media`（news-row）或 `figure.thumb`（topic）；建议 HTML 顺序为「正文块 → 图」。模板会做成文左图右，点击可放大——不必在 fragment 里写灯箱。
- `meta.json.health_line` = JSON 里的 `summary.health_line`。

## 引证 Badge（x-ai 话题 / design / news）

```html
<article class="topic">
  <h3 class="topic-title">话题名</h3>
  <p class="topic-lead">一句话结论（中文）</p>
  <figure class="thumb"><img src="…" alt="" loading="lazy"></figure><!-- 可选，放正文后 -->
  <div class="cite-badges">
    <button type="button" class="cite-badge" data-cite-id="xa-1">Sam Altman</button>
  </div>
  <div id="cite-xa-1" class="cite-panel" hidden>
    <p class="cite-zh">中文引证（英文必须翻译）</p>
    <p class="cite-meta">source_name · pub_date</p>
    <a class="cite-link" href="原帖link" target="_blank" rel="noopener">查看原文</a>
  </div>
</article>
```

- `data-cite-id` 与 `id="cite-…"` 对应（前缀 `xa-` / `de-` / `ne-`）。
- **资源链接**不用 badge，见下。

## aihot

主 agent 跑 `render_aihot_fragment.py` 即可（`feed.xml` 已含摘要与分类）。**不要**开子 agent，也**不要**浏览器抓页面。

## x-ai

不要梯队、不要统计表。

1. 核心信号（2–3）
2. 热点话题（3–6 簇）
3. **尝试与教程**（必填；没有则写「今日未见突出尝试/教程」）
4. 潜在线索（最多 4）
5. **资源链接**直接罗列：

```html
<h2 class="section-head">资源链接</h2>
<ul class="resource-list">
  <li>
    <a href="URL" target="_blank" rel="noopener">标题或路径</a>
    <span class="resource-meta">博主 · 一句话</span>
  </li>
</ul>
```

## design（灵感向）

产品 / 视觉 / 趋势 / 装置优先，建筑降权。结构：今日灵感焦点 → 话题簇 → 趋势线索。引证用 badge。

## news

事件聚合；今日要闻 + 热点话题。引证用 badge。

## health

由 `compose_digest.py` 生成：x-ai / design / news 分组可折叠；无 AIHOT 行。
