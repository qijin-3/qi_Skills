---
name: daily-news-digest
version: 1.4.0
description: >
  生成每日资讯日报 HTML（四 Tab：AIHOT / X-AI / 设计 / 今日新闻 + 订阅源健康）。
  用户说「资讯日报」「今日资讯日报」「生成日报」「daily news digest」「抓一下 RSS 日报」
  「AIHOT 和 X 博主今天说了什么」「出一份设计早报+新闻合集」时务必使用本技能——即使只提了其中一个板块，
  也应按完整四板块流程跑（除非用户明确只要某一栏）。过去 24 小时窗口；X 源带 Nitter mirror 兜底。
compatibility: 需要联网；Python 3.10+（标准库即可）；Cursor Task/子 agent 并行写稿
---

# Daily News Digest

把 AIHOT + X 博主 + 设计 RSS + 新闻 RSS 聚合成**一份带 Tab 的 HTML 日报**。

**分工**：抓取 / 过滤 / 组装 / AIHOT 渲染 → 脚本（细节看脚本本身，SKILL 不复述）；话题写稿与分类 → 子 agent + `section-specs.md`；样式 → 只填模板占位符。

## 路径

| 用途 | 路径 |
|------|------|
| 技能根 | 本文件所在目录 `{SKILL}` |
| 订阅清单 | `{SKILL}/references/feeds.json` |
| 写稿规格 | `{SKILL}/references/section-specs.md` |
| HTML 壳 | `{SKILL}/assets/template.html` |
| 默认输出 | `~/Desktop/daily-news-digest/{YYYY-MM-DD}/` |

```text
{YYYY-MM-DD}/
├── raw/          # fetch_section 产出
├── sections/     # *.fragment.html + *.meta.json
└── index.html
```

## 工作流

### 0. 准备

`DATE=YYYY-MM-DD`（用户指定则用用户的）→ `mkdir -p ~/Desktop/daily-news-digest/$DATE/{raw,sections}` → Read `section-specs.md`。

### 1. 抓取

```bash
python3 "{SKILL}/scripts/fetch_section.py" --all --hours 24 \
  --out ~/Desktop/daily-news-digest/$DATE/raw
```

再渲染 AIHOT（读 `raw/aihot.json`，按分类出 fragment，**不要**开浏览器）：

```bash
python3 "{SKILL}/scripts/render_aihot_fragment.py" \
  --raw ~/Desktop/daily-news-digest/$DATE/raw/aihot.json \
  --out-dir ~/Desktop/daily-news-digest/$DATE/sections \
  --date "$DATE"
```

### 2. 三个子 agent 并行写稿（X-AI / 设计 / 新闻）

同一回合起 3 个 Task。各自只读对应 `raw/*.json` + `section-specs.md`，写入 `sections/`。

要点（细节在 specs）：只根据 JSON 写、不编造；用 `.topic` / `.cite-badge` / `.news-row` / `.resource-list`；有图时 figure 用 `.thumb` 或 `.news-media`（模板会排成文左图右并可点大图）；`meta.json.health_line` 抄 `summary.health_line`；X-AI 必有「尝试与教程」，资源链接用 `ul.resource-list`。

### 3. 组装

```bash
python3 "{SKILL}/scripts/compose_digest.py" \
  --out ~/Desktop/daily-news-digest/$DATE \
  --date "$DATE"
```

### 4. 交付

告知绝对路径并用 `open` 打开；附四行健康摘要。脚本已处理的镜像失败等细节，只报数量即可。

## 用户变体

- 只要某一栏 → 仍建议 `--all` 抓取（健康表完整），写稿可只开对应子 agent。
- 换输出目录 → 用户路径，结构仍是 `raw/` + `sections/` + `index.html`。
- 换主题 → 仅用户点名时改模板；默认不动。

## 自检

- [ ] `<title>` 是日期；五个 Tab 可切
- [ ] AIHOT 有正文摘要（非空壳）；非 AIHOT 顶栏有健康句
- [ ] 健康 Tab 无 AIHOT 行；链接可点、无 JSON 外假新闻
- [ ] 有图条目文左图右；点图可放大
