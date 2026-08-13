# qi Skills

我的 agent skills 集合，用于日常工程实践和生产力提升。

## 快速开始

### 克隆仓库

```bash
git clone https://github.com/jin-dev/qi_Skills.git ~/qi_Skills
```

### 通过 AI Agent 安装

直接对你的 AI Agent 说：

- "安装 jin-dev/qi_Skills" — 安装所有 skills
- "安装 jin-dev/qi_Skills 的 idea-validator skill" — 安装单个 skill

Agent 会自动处理克隆与安装。

### 更新技能目录

增删技能后，运行：

```bash
cd ~/qi_Skills
python3 scripts/skills-registry.py readme
```

## Skills 目录

仓库内全部技能如下。

```
skills/
├── career/
│   └── interview-coach/  — High-rigor interview coaching skill for…
├── design/
│   ├── ai-design-reviewer/  — AI 功能设计评审工具
│   └── ui-copy/  — UI Copy
├── dev/
│   ├── ali-deploy-guide-generator/  — 根据项目技术栈生成阿里云 ECS 部署方案与 GitHub 自动化部署配置
│   └── ecs-server-manager/  — 阿里云 ECS 服务器运维管理工具
├── havefun/
│   └── travel-journal/  — 游记生成器
├── product/
│   ├── 10x-impact-judge/  — 10倍影响力判断器
│   ├── ai-user-research/  — AI-powered user research analysis techniques…
│   ├── brainstorm/  — 头脑风暴 · 传播型想法共创
│   ├── deep-research/  — 深度调研方法论（8步法）
│   ├── idea-agile-assessment/  — 想法敏捷评估
│   ├── idea-validator/  — 面向独立开发者 / 早期创业者
│   └── product-namer/  — 产品命名专家
└── tools/
    ├── daily-news-digest/  — 生成每日资讯日报 HTML（四 Tab
    ├── meeting/  — 会议录音与逐字稿整理
    ├── skill-manager/  — 管理 ~/.agents/skills 软链接与 ~/Skill Manager…
    ├── tunnel-serve/  — Expose local HTML files or…
    └── wechat-doubler/  — macOS 微信双开工具
```

### Career

`skills/career/`

- **[interview-coach](./skills/career/interview-coach/SKILL.md)** — High-rigor interview coaching skill for…

### Design

`skills/design/`

- **[ai-design-reviewer](./skills/design/ai-design-reviewer/SKILL.md)** — AI 功能设计评审工具
- **[ui-copy](./skills/design/ui-copy/SKILL.md)** — UI Copy

### Dev

`skills/dev/`

- **[ali-deploy-guide-generator](./skills/dev/ali-deploy-guide-generator/SKILL.md)** — 根据项目技术栈生成阿里云 ECS 部署方案与 GitHub 自动化部署配置
- **[ecs-server-manager](./skills/dev/ecs-server-manager/SKILL.md)** — 阿里云 ECS 服务器运维管理工具

### Havefun

`skills/havefun/`

- **[travel-journal](./skills/havefun/travel-journal/SKILL.md)** — 游记生成器

### Product

`skills/product/`

- **[10x-impact-judge](./skills/product/10x-impact-judge/SKILL.md)** — 10倍影响力判断器
- **[ai-user-research](./skills/product/ai-user-research/SKILL.md)** — AI-powered user research analysis techniques…
- **[brainstorm](./skills/product/brainstorm/SKILL.md)** — 头脑风暴 · 传播型想法共创
- **[deep-research](./skills/product/deep-research/SKILL.md)** — 深度调研方法论（8步法）
- **[idea-agile-assessment](./skills/product/idea-agile-assessment/SKILL.md)** — 想法敏捷评估
- **[idea-validator](./skills/product/idea-validator/SKILL.md)** — 面向独立开发者 / 早期创业者
- **[product-namer](./skills/product/product-namer/SKILL.md)** — 产品命名专家

### Tools

`skills/tools/`

- **[daily-news-digest](./skills/tools/daily-news-digest/SKILL.md)** — 生成每日资讯日报 HTML（四 Tab
- **[meeting](./skills/tools/meeting/SKILL.md)** — 会议录音与逐字稿整理
- **[skill-manager](./skills/tools/skill-manager/SKILL.md)** — 管理 ~/.agents/skills 软链接与 ~/Skill Manager…
- **[tunnel-serve](./skills/tools/tunnel-serve/SKILL.md)** — Expose local HTML files or…
- **[wechat-doubler](./skills/tools/wechat-doubler/SKILL.md)** — macOS 微信双开工具

## License

AGPL-3.0 — See [LICENSE](./LICENSE) for details.
