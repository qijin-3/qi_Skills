# qi Skills

我的 agent skills 集合，用于日常工程实践和生产力提升。

## 快速开始 (30秒配置)

### 方式一：克隆并安装所有 skills

```bash
# 克隆仓库
git clone https://github.com/jin-dev/qi_Skills.git ~/qi_Skills

# 运行链接脚本
cd ~/qi_Skills
./scripts/link-skills.sh
```

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

### Uncategorized

- **[travel-journal](./skills/travel-journal/SKILL.md)** — 游记生成器 - 帮助用户从零开始创建一个基于地图的互动旅行游记网站（静态 HTML，无需服务器）

## License

AGPL-3.0 — See [LICENSE](./LICENSE) for details.
