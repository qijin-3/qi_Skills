# 技能同步配置说明

唯一配置文件：`skills-sync.yaml`（仓库根目录）

## 格式

```yaml
sync:
  - 10x-impact-judge
  - idea-validator

unsync:
  - meeting
  - travel-journal
```

- **sync** — 会软链接到 `~/.claude/skills/`
- **unsync** — 仅登记在仓库，不安装到本地 Claude Code

在两组之间**复制粘贴** `name` 即可切换。`name` 来自 SKILL.md frontmatter，不是目录名。

## 目录结构与嵌套技能

```
skills/
├── meeting/                  # 单技能
│   └── SKILL.md
├── product design/           # 分组目录
│   ├── idea-validator/
│   │   └── SKILL.md
│   └── deep-research/
│       └── SKILL.md
└── travel_journal/
    ├── travel-journal/
    └── install-travel-journal/
```

扫描规则：递归查找所有 `SKILL.md`，排除 `deprecated/`、`node_modules/`、`template/`。

软链接名始终使用 frontmatter 的 `name`。

## 工作流

1. 在 `skills/` 下创建技能
2. 运行 `python3 scripts/skills-registry.py all`
   - 新技能自动加入 `unsync`
   - README 自动更新
   - sync 组中的技能创建软链接
3. 要发布技能：将 `name` 从 `unsync` 移到 `sync`，再运行 `all`

## 同步与软链接清理

运行 `sync` 或 `all` 时会：

- 为 `sync` 组中的技能创建/更新软链接
- **移除**已移到 `unsync` 的技能软链接
- 扫描 `~/.claude/skills/`，清理所有指向本仓库但不在 `sync` 组的残留链接
