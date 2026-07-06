---
name: meeting
description: |
  会议录音与逐字稿整理：自动分组、重命名、归档，并按模板生成结构化会议纪要。
  只要用户提到整理会议纪要、处理会议录音、归档逐字稿、批量生成纪要，或 Downloads 里有「录音YYYY-MM-DD」文件，就应使用本技能——即使用户没说「meeting skill」。
  触发词：整理会议纪要、处理会议录音、会议归档、逐字稿转纪要、帮我整理会议文件。
---

# 会议纪要整理

处理会议录音和逐字稿：脚本负责文件整理与归档，AI 负责按模板生成纪要。

## 工作流程

1. **运行脚本** — 扫描源目录，按日期分组、复制录音、重命名逐字稿、归档
2. **生成纪要** — 读取模板，为每个逐字稿生成对应会议纪要
3. **确认结果** — 检查归档目录中录音、逐字稿、纪要三者序号一致

默认源目录：`~/Downloads`。用户指定路径时替换即可。

## 快速使用

用户说「帮我整理会议纪要」时：

1. 在技能目录执行 `python3 scripts/process_meetings.py [源目录]`
2. Read `references/meeting-minutes-template.md`，批量读取归档目录下各日期文件夹中的逐字稿，并行生成纪要
3. 纪要命名：`逐字稿2026-01-09-1.md` → `会议纪要2026-01-09-1.md`（同目录、同序号）

跳过归档：`python3 scripts/process_meetings.py --no-archive`

## 何时读取参考文件

| 场景 | 读取 |
|------|------|
| 生成会议纪要前 | `references/meeting-minutes-template.md` |
| 文件名/配对疑问 | `references/file-naming.md` |
| 配置归档路径等 | `references/config.md` |
| 脚本报错或找不到文件 | `references/troubleshooting.md` |

## 脚本命令

```bash
# 默认处理 ~/Downloads 并归档
python3 scripts/process_meetings.py

# 指定源目录
python3 scripts/process_meetings.py ~/Desktop/meetings

# 创建配置文件（config.json）
python3 scripts/process_meetings.py --create-config

# 自定义配置
python3 scripts/process_meetings.py -c config.json
```

## 安全特性

- 默认不覆盖已存在文件（`skip_existing: true`）
- 自动校验日期格式有效性
- 重要操作前可询问用户确认
