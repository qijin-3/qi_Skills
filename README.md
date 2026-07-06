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
│   └── ai-design-reviewer/  — AI 功能设计评审工具
├── dev/
│   ├── ali-deploy-guide-generator/  — 根据项目技术栈生成阿里云 ECS 部署方案与 GitHub 自动化部署配置
│   └── ecs-server-manager/  — 阿里云 ECS 服务器运维管理工具
├── havefun/
│   └── travel-journal/  — 游记生成器
├── health_os/
│   ├── health-coach/  — 飞书健康教练
│   ├── health-daily-remind/  — 健康每日提醒
│   ├── health-evening-close/  — 健康每日晚间收口
│   ├── health-monthly-review/  — 健康月复盘
│   ├── health-weekly-plan/  — 健康周计划
│   └── health-weekly-review/  — 健康周反馈
├── personal_os/
│   ├── annual-review/  — 北极星管理与年度复盘的统一入口
│   ├── daily-briefing/  — 每日早报调度
│   ├── diary-capture/  — 日记碎片捕获入口
│   ├── evening-review/  — 每日晚报收尾
│   ├── monthly-plan/  — 月度目标规划
│   ├── monthly-review/  — 月度复盘
│   ├── quick-task/  — 飞书任务捕获入口
│   ├── weekly-plan/  — 下周计划安排
│   └── weekly-review/  — 周复盘
├── product/
│   ├── 10x-impact-judge/  — 10倍影响力判断器
│   ├── ai-user-research/  — AI-powered user research analysis techniques…
│   ├── brainstorm/  — 头脑风暴 · 传播型想法共创
│   ├── deep-research/  — 深度调研方法论（8步法）
│   ├── idea-agile-assessment/  — 想法敏捷评估
│   ├── idea-validator/  — Idea 快速验证工具
│   └── product-namer/  — 产品命名专家
└── tools/
    ├── meeting/  — 自动整理会议相关文件
    ├── tunnel-serve/  — Expose local HTML files or…
    └── wechat-doubler/  — macOS 微信双开工具
```

### Career

`skills/career/`

- **[interview-coach](./skills/career/interview-coach/SKILL.md)** — High-rigor interview coaching skill for…

### Design

`skills/design/`

- **[ai-design-reviewer](./skills/design/ai-design-reviewer/SKILL.md)** — AI 功能设计评审工具

### Dev

`skills/dev/`

- **[ali-deploy-guide-generator](./skills/dev/ali-deploy-guide-generator/SKILL.md)** — 根据项目技术栈生成阿里云 ECS 部署方案与 GitHub 自动化部署配置
- **[ecs-server-manager](./skills/dev/ecs-server-manager/SKILL.md)** — 阿里云 ECS 服务器运维管理工具

### Havefun

`skills/havefun/`

- **[travel-journal](./skills/havefun/travel-journal/SKILL.md)** — 游记生成器

### Health OS

`skills/health_os/`

- **[health-coach](./skills/health_os/health-coach/SKILL.md)** — 飞书健康教练
- **[health-daily-remind](./skills/health_os/health-daily-remind/SKILL.md)** — 健康每日提醒
- **[health-evening-close](./skills/health_os/health-evening-close/SKILL.md)** — 健康每日晚间收口
- **[health-monthly-review](./skills/health_os/health-monthly-review/SKILL.md)** — 健康月复盘
- **[health-weekly-plan](./skills/health_os/health-weekly-plan/SKILL.md)** — 健康周计划
- **[health-weekly-review](./skills/health_os/health-weekly-review/SKILL.md)** — 健康周反馈

### Personal OS

`skills/personal_os/`

- **[annual-review](./skills/personal_os/annual-review/SKILL.md)** — 北极星管理与年度复盘的统一入口
- **[daily-briefing](./skills/personal_os/daily-briefing/SKILL.md)** — 每日早报调度
- **[diary-capture](./skills/personal_os/diary-capture/SKILL.md)** — 日记碎片捕获入口
- **[evening-review](./skills/personal_os/evening-review/SKILL.md)** — 每日晚报收尾
- **[monthly-plan](./skills/personal_os/monthly-plan/SKILL.md)** — 月度目标规划
- **[monthly-review](./skills/personal_os/monthly-review/SKILL.md)** — 月度复盘
- **[quick-task](./skills/personal_os/quick-task/SKILL.md)** — 飞书任务捕获入口
- **[weekly-plan](./skills/personal_os/weekly-plan/SKILL.md)** — 下周计划安排
- **[weekly-review](./skills/personal_os/weekly-review/SKILL.md)** — 周复盘

### Product

`skills/product/`

- **[10x-impact-judge](./skills/product/10x-impact-judge/SKILL.md)** — 10倍影响力判断器
- **[ai-user-research](./skills/product/ai-user-research/SKILL.md)** — AI-powered user research analysis techniques…
- **[brainstorm](./skills/product/brainstorm/SKILL.md)** — 头脑风暴 · 传播型想法共创
- **[deep-research](./skills/product/deep-research/SKILL.md)** — 深度调研方法论（8步法）
- **[idea-agile-assessment](./skills/product/idea-agile-assessment/SKILL.md)** — 想法敏捷评估
- **[idea-validator](./skills/product/idea-validator/SKILL.md)** — Idea 快速验证工具
- **[product-namer](./skills/product/product-namer/SKILL.md)** — 产品命名专家

### Tools

`skills/tools/`

- **[meeting](./skills/tools/meeting/SKILL.md)** — 自动整理会议相关文件
- **[tunnel-serve](./skills/tools/tunnel-serve/SKILL.md)** — Expose local HTML files or…
- **[wechat-doubler](./skills/tools/wechat-doubler/SKILL.md)** — macOS 微信双开工具

## License

AGPL-3.0 — See [LICENSE](./LICENSE) for details.
