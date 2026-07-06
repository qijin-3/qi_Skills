# 设备配置文件 Schema

路径：`~/Skill Manager/configs/<device-id>.json`

```json
{
  "version": 1,
  "device_id": "macbook-pro",
  "repos": [
    {
      "id": "jin-dev/qi_Skills",
      "url": "https://github.com/jin-dev/qi_Skills.git",
      "branch": "main",
      "cache_path": ".cache/repos/jin-dev-qi_Skills",
      "last_commit": "abc123def456...",
      "skills": [
        {
          "name": "meeting",
          "source_path": "skills/tools/meeting",
          "installed_commit": "abc123def456...",
          "sync": true
        }
      ]
    }
  ]
}
```

## 字段说明

| 字段 | 说明 |
|------|------|
| `device_id` | 设备标识，与文件名一致 |
| `repos[].id` | GitHub `owner/repo` |
| `repos[].alias` | 可选显示别名 |
| `repos[].cache_path` | 相对于 `~/Skill Manager` 的 git 缓存路径 |
| `repos[].last_commit` | 仓库上次 fetch 的 commit SHA |
| `skills[].name` | SKILL.md frontmatter 中的 `name` |
| `skills[].source_path` | 技能在仓库内的相对路径 |
| `skills[].installed_commit` | 该技能上次安装/更新的 commit |
| `skills[].sync` | `true` = 本设备已同步到 `Skills/` 目录 |
