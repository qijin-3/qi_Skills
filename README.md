# qi Skills

我的 agent skills 集合，用于日常工程实践和生产力提升。

## 快速开始 (30秒配置)

### 方式一：克隆并按注册表同步 skills

```bash
# 克隆仓库
git clone https://github.com/jin-dev/qi_Skills.git ~/qi_Skills

# 按 skills-registry.yaml 中 sync=true 的条目软链接到 Claude Code
cd ~/qi_Skills
python3 scripts/skills-registry.py all
```

注册表 `skills-registry.yaml` 列出仓库内所有技能；只有标记 `sync: true` 的会安装到 `~/.claude/skills/`。
要发布新技能，编辑注册表后将对应条目的 `sync` 改为 `true`，再重新运行上述命令。

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

## Skills 列表

### Travel Journal

- **[travel-journal](./skills/travel_journal/travel-journal/SKILL.md)** — 游记生成器 - 帮助用户从零开始创建一个基于地图的互动旅行游记网站（静态 HTML，无需服务器）。 当用户说"创建游记"、"生成旅行日记"、"travel journal"、"旅行网站"、"帮我做游记"、 "记录我的旅途"、"制作行程地图"时立即触发。 也支持对已有游记项目进行后期修改（添加行程、更新日记、重跑照片匹配、更换风格）。 检测到用户目录中有 data/days.json 时自动进入更新模式。 只要用户提到游记、旅行记录、行程可视化，都应使用此技能。

### Uncategorized

- **[idea-validator](./skills/idea-validator/SKILL.md)** — Idea 快速验证工具 - 通过结构化多步骤方法论帮助独立开发者在投入开发前验证产品想法。 覆盖危险信号预筛 → 假设锁定 → 用户声音挖掘（7 平台）→ 竞品解构 → 综合评估的完整流程，最终输出可视化 HTML 报告。 当用户说「验证这个 idea」「分析这个产品想法」「帮我做市场调研」「这个方向值得做吗」「我有个想法」「走赛道 A」「这个产品可行吗」，或者直接描述一个产品/创业想法时触发。

## License

AGPL-3.0 — See [LICENSE](./LICENSE) for details.
