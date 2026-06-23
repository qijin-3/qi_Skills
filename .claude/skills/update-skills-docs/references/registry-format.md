# 技能注册表格式说明

注册表文件：`skills-registry.yaml`（仓库根目录）

## 字段

| 字段 | 来源 | 说明 |
|------|------|------|
| `path` | 自动 | 技能目录，相对仓库根目录，如 `skills/travel_journal/travel-journal` |
| `name` | 自动 | SKILL.md frontmatter 的 `name`，也是 `~/.claude/skills/` 下的软链接名 |
| `description` | 自动 | 从 SKILL.md frontmatter 提取并压缩为单行 |
| `category` | 自动 | 根据目录结构推断（见下方规则） |
| `sync` | **手动** | `true` = 同步到 Claude Code；`false` = 仅登记 |

## 目录结构与嵌套技能

`skills/` 下技能可能出现在不同深度：

```
skills/
├── idea-validator/           # 直接子目录 → category: uncategorized
│   └── SKILL.md
├── engineering/
│   └── my-skill/             # 分类目录 → category: engineering
│       └── SKILL.md
└── travel_journal/           # 分组目录（非技能本身）
    ├── travel-journal/       # → category: travel_journal
    │   └── SKILL.md
    └── install-travel-journal/
        └── SKILL.md
```

扫描规则：递归查找所有 `SKILL.md`，排除 `deprecated/`、`node_modules/`、`template/` 路径。

软链接名始终使用 frontmatter 的 `name`，**不是**目录 basename。例如 `travel_journal/travel-journal/` 链接为 `~/.claude/skills/travel-journal`。

## Category 推断

1. 路径仅一段（`skills/foo`）→ `uncategorized`
2. 首段为已知分类（`engineering`、`productivity`、`misc`）→ 使用该分类
3. 其他多段路径 → 首段作为分组名（如 `travel_journal`）

## 手动操作

新增技能后运行扫描，新条目默认 `sync: false`。要发布到 Claude Code：

1. 编辑 `skills-registry.yaml`，将对应技能的 `sync` 改为 `true`
2. 运行 `python scripts/skills-registry.py all`

取消同步：将 `sync` 改为 `false` 后重新运行 sync，脚本会自动移除指向本仓库的失效软链接。
