# 各板块写作规格

子 agent **只根据**对应 `raw/*.json` 写稿，禁止编造。抓取与过滤结果以 JSON 为准。

## 共用

- 结构：`.section-head` + `.news-row` 或 `.topic` + cite-badge。
- 有 `image`：正文块后接 `.news-media` 或 `figure.thumb`（布局由模板处理）。
- `meta.json.health_line` = JSON 的 `summary.health_line`。

## 引证 Badge（x-ai / design / news）

```html
<article class="topic">
  <h3 class="topic-title">话题名</h3>
  <p class="topic-lead">一句话结论（中文）</p>
  <figure class="thumb"><img src="…" alt="" loading="lazy"></figure><!-- 可选 -->
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
- 资源链接不用 badge。

## aihot

主 agent 跑 `render_aihot_fragment.py`；不开子 agent。

## x-ai

1. 核心信号（2–3）
2. 热点话题（3–6 簇）
3. **尝试与教程**（必填；没有则写「今日未见突出尝试/教程」）
4. 潜在线索（最多 4）
5. **资源链接**：

```html
<h2 class="section-head">资源链接</h2>
<ul class="resource-list">
  <li>
    <a href="URL" target="_blank" rel="noopener">标题或路径</a>
    <span class="resource-meta">博主 · 一句话</span>
  </li>
</ul>
```

## design

产品 / 视觉 / 趋势 / 装置优先，建筑降权。今日灵感焦点 → 话题簇 → 趋势线索。

## news

事件聚合：今日要闻 + 热点话题。
