# meeting

会议录音与逐字稿整理技能。完整说明见 [SKILL.md](SKILL.md)。

## 目录结构

```
meeting/
├── SKILL.md
├── config.example.json
├── references/
│   ├── meeting-minutes-template.md   # 纪要生成模板
│   ├── file-naming.md                # 命名规范
│   ├── config.md                     # 配置说明
│   └── troubleshooting.md            # 故障排除
└── scripts/
    └── process_meetings.py
```

## 快速开始

```
帮我整理会议纪要
```

或手动：

```bash
cp config.example.json config.json   # 首次使用
python3 scripts/process_meetings.py
```
