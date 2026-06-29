# qi Skills

我的 agent skills 集合，用于日常工程实践和生产力提升。

## 快速开始 (30秒配置)

### 方式一：克隆并按 skills-sync.yaml 同步

```bash
# 克隆仓库
git clone https://github.com/jin-dev/qi_Skills.git ~/qi_Skills

# 按 skills-sync.yaml 配置软链接到 Claude Code
cd ~/qi_Skills
python3 scripts/skills-registry.py all
```

编辑 `skills-sync.yaml`，在 `sync` / `unsync` 两组之间移动技能 `name`，再重新运行上述命令。

### 方式二：通过 AI Agent 直接安装

直接对你的 AI Agent 说：

- "安装 jin-dev/qi_Skills" - 安装所有 skills
- "安装 jin-dev/qi_Skills 的 grill-me skill" - 安装单个 skill

Agent 会自动处理克隆、定位、链接等操作。

### 方式三：手动链接单个 skill

```bash
cd ~/.claude/skills
ln -s ~/qi_Skills/skills/<skill-name> <skill-name>
```

## Skills 目录

仓库内全部技能如下。带 `[已同步]` 的会安装到 `~/.claude/skills/`（在 `skills-sync.yaml` 的 `sync` 组）。

```
skills/
├── design/
│   └── guizang-social-card-skill-main/  — Generate Guizang-style social card image…
├── meeting/  — 自动整理会议相关文件
├── personal_management/
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
│   ├── 10x-impact-judge/ [已同步]  — 10倍影响力判断器
│   ├── ai-design-reviewer/ [已同步]  — AI 功能设计评审工具
│   ├── ai-user-research/ [已同步]  — AI-powered user research analysis techniques…
│   ├── brainstorm/ [已同步]  — 头脑风暴 · 传播型想法共创
│   ├── deep-research/ [已同步]  — 深度调研方法论（8步法）
│   ├── idea-agile-assessment/ [已同步]  — 想法敏捷评估
│   └── idea-validator/ [已同步]  — Idea 快速验证工具
└── travel_journal/
    ├── install-travel-journal/  — Travel Journal 安装引导
    └── travel-journal/  — 游记生成器
```

### Design

`skills/design/`

- **[guizang-social-card-skill](./skills/design/guizang-social-card-skill-main/SKILL.md)** — Generate Guizang-style social card image…

### Meeting

`skills/meeting/`

- **[meeting](./skills/meeting/SKILL.md)** — 自动整理会议相关文件

### Personal Management

`skills/personal_management/`

- **[annual-review](./skills/personal_management/annual-review/SKILL.md)** — 北极星管理与年度复盘的统一入口
- **[daily-briefing](./skills/personal_management/daily-briefing/SKILL.md)** — 每日早报调度
- **[diary-capture](./skills/personal_management/diary-capture/SKILL.md)** — 日记碎片捕获入口
- **[evening-review](./skills/personal_management/evening-review/SKILL.md)** — 每日晚报收尾
- **[monthly-plan](./skills/personal_management/monthly-plan/SKILL.md)** — 月度目标规划
- **[monthly-review](./skills/personal_management/monthly-review/SKILL.md)** — 月度复盘
- **[quick-task](./skills/personal_management/quick-task/SKILL.md)** — 飞书任务捕获入口
- **[weekly-plan](./skills/personal_management/weekly-plan/SKILL.md)** — 下周计划安排
- **[weekly-review](./skills/personal_management/weekly-review/SKILL.md)** — 周复盘

### Product

`skills/product/`

- **[10x-impact-judge](./skills/product/10x-impact-judge/SKILL.md)** `[已同步]` — 10倍影响力判断器
- **[ai-design-reviewer](./skills/product/ai-design-reviewer/SKILL.md)** `[已同步]` — AI 功能设计评审工具
- **[ai-user-research](./skills/product/ai-user-research/SKILL.md)** `[已同步]` — AI-powered user research analysis techniques…
- **[brainstorm](./skills/product/brainstorm/SKILL.md)** `[已同步]` — 头脑风暴 · 传播型想法共创
- **[deep-research](./skills/product/deep-research/SKILL.md)** `[已同步]` — 深度调研方法论（8步法）
- **[idea-agile-assessment](./skills/product/idea-agile-assessment/SKILL.md)** `[已同步]` — 想法敏捷评估
- **[idea-validator](./skills/product/idea-validator/SKILL.md)** `[已同步]` — Idea 快速验证工具

### Travel Journal

`skills/travel_journal/`

- **[install-travel-journal](./skills/travel_journal/install-travel-journal/SKILL.md)** — Travel Journal 安装引导
- **[travel-journal](./skills/travel_journal/travel-journal/SKILL.md)** — 游记生成器

## License

AGPL-3.0 — See [LICENSE](./LICENSE) for details.
