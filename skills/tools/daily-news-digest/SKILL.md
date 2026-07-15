---
name: daily-news-digest
version: 1.5.0
description: >
  生成每日资讯日报 HTML（四 Tab：AIHOT / X-AI / 设计 / 今日新闻 + 订阅源健康）；
  也用于「添加订阅源」「加一个 RSS/X 博主到日报」。用户说「资讯日报」「生成日报」
  「daily news digest」「加订阅源」「把某某 RSS 加进设计日报」时务必使用本技能。
  输出落在 Agent 空间或当前工作目录下的 daily-news-digest/（可被环境变量覆盖）。
compatibility: 需要联网；Python 3.10+（标准库即可）；子 agent 并行写稿
---

# Daily News Digest

抓取 / 过滤 / AIHOT 渲染 / 组装 / 加源 → **脚本**；话题写稿 → 子 agent + `section-specs.md`。

## 输出路径（通用规则）

先解析根目录，再按日期落盘。**不要写死 Desktop**。

优先级（`scripts/paths.py` / `resolve_out.py`）：

1. CLI `--root`
2. 环境变量 `DAILY_NEWS_DIGEST_ROOT`
3. 检测到的 Agent workspace（`OPENCLAW_WORKSPACE_DIR` / `QCLAW_*` / 含 `AGENTS.md` 等标记的 cwd）→ `{workspace}/daily-news-digest`
4. 否则 → `{cwd}/daily-news-digest`

当日目录：

```text
{DIGEST_ROOT}/{YYYY-MM-DD}/
├── raw/
├── sections/
└── index.html
```

```bash
eval "$(python3 "{SKILL}/scripts/resolve_out.py" --date "$DATE" --mkdir)"
# 得到 DIGEST_ROOT / DIGEST_DAY / DIGEST_RAW / DIGEST_SECTIONS / DIGEST_INDEX
```

## 添加订阅源

```bash
# 自动分类到 aihot / x-ai / design / news
python3 "{SKILL}/scripts/add_feed.py" --url "https://example.com/feed.xml" --name "示例源"

# X 博主 → x-ai
python3 "{SKILL}/scripts/add_feed.py" --handle someone --name "Someone"

# 强制板块
python3 "{SKILL}/scripts/add_feed.py" --url "..." --section design --domain "产品/工业设计"

# 仅预览分类 / 列出
python3 "{SKILL}/scripts/add_feed.py" --url "..." --classify-only
python3 "{SKILL}/scripts/add_feed.py" --list
```

写入 `{SKILL}/references/feeds.json`。下次生成日报自动带上。

## 生成日报

```bash
DATE=YYYY-MM-DD   # 用户指定则用之
eval "$(python3 "{SKILL}/scripts/resolve_out.py" --date "$DATE" --mkdir)"
# Read section-specs.md

python3 "{SKILL}/scripts/fetch_section.py" --all --hours 24 --out "$DIGEST_RAW"

python3 "{SKILL}/scripts/render_aihot_fragment.py" \
  --raw "$DIGEST_RAW/aihot.json" --out-dir "$DIGEST_SECTIONS" --date "$DATE"

# 同一回合 3 个子 agent：x-ai / design / news → $DIGEST_SECTIONS
# 约束见 section-specs.md；只根据 raw JSON 写，不编造

python3 "{SKILL}/scripts/compose_digest.py" --out "$DIGEST_DAY" --date "$DATE"
```

交付：告知 `$DIGEST_INDEX` 绝对路径；附健康摘要行。

## 资产

| 用途 | 路径 |
|------|------|
| 订阅清单 | `{SKILL}/references/feeds.json` |
| 写稿规格 | `{SKILL}/references/section-specs.md` |
| HTML 壳 | `{SKILL}/assets/template.html` |
