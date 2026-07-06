---
name: meeting
description: 自动整理会议相关文件，包括会议录音和逐字稿，并在生成结构化会议纪后归档到指定文件夹。支持多种音频格式，自动归档，文件保护。
---

# 会议纪要整理

## 概述

处理会议录音文件和逐字稿，自动生成会议纪要并按日期归档。

**工作流程**：
1. Python 脚本处理文件（分组、复制、重命名逐字稿）
2. AI 根据模板生成会议纪要
3. **自动**移动日期文件夹到归档目录

**前提**：
- 录音文件已手工命名：`录音2026-01-09-1.m4a`（支持 .m4a, .mp3, .wav, .aac, .ogg, .flac, .wma 等音频格式）
- 逐字稿文件格式：`录音2026-01-09-1_原文.md`

## 新功能 v2.0

✨ **自动归档**：处理完成后自动移动到归档目录
🔒 **文件保护**：跳过已存在文件，避免意外覆盖
📅 **日期验证**：自动验证日期格式有效性
⚙️ **配置文件**：支持自定义配置文件

## 使用方法

### 快速使用

告诉 AI 助手：
```
帮我整理会议纪要
```

AI 会自动使用 **~/Downloads** 文件夹（默认）：
1. 运行 Python 脚本处理文件
2. 读取模板，调用大模型生成会议纪要
3. **自动**移动日期文件夹到归档目录

如果会议文件在其他位置，可以指定路径：
```
帮我整理 <源文件夹路径> 下的会议纪要
```

### 手动执行

**第1步**：运行脚本处理文件

```bash
# 默认处理 ~/Downloads 文件夹并自动归档
python3 ~/.claude/skills/meeting/scripts/process_meetings.py

# 指定源文件夹
python3 ~/.claude/skills/meeting/scripts/process_meetings.py ~/Desktop/meetings

# 跳过自动归档（只处理不归档）
python3 ~/.claude/skills/meeting/scripts/process_meetings.py --no-archive

# 使用自定义配置文件
python3 ~/.claude/skills/meeting/scripts/process_meetings.py -c /path/to/config.json
```

**高级选项**：
```bash
# 创建默认配置文件
python3 ~/.claude/skills/meeting/scripts/process_meetings.py --create-config

# 查看帮助信息
python3 ~/.claude/skills/meeting/scripts/process_meetings.py --help
```

**第2步**：调用大模型生成会议纪要

建议使用**批量处理**方式(提速):
```
批量读取 <归档目录> 下所有日期文件夹中的逐字稿文件，然后根据模板 会议纪要生成.md 为每个逐字稿生成对应的会议纪要
```

生成规则:
- 生成文件命名规范：`会议纪要YYYY-MM-DD-N.md`（序号与逐字稿一致）
- 可以一次性读取所有逐字稿,然后并行生成所有纪要(提速)
- 示例：
  - `逐字稿2026-01-09-1.md` → 生成 `会议纪要2026-01-09-1.md`
  - `逐字稿2026-01-09-2.md` → 生成 `会议纪要2026-01-09-2.md`

### 文件命名规范

**录音文件**（手工命名，支持多种音频格式）：
- 支持格式：`.m4a`, `.mp3`, `.wav`, `.aac`, `.ogg`, `.flac`, `.wma`
- 单个会议：`录音2026-01-08.m4a` 或 `录音2026-01-08.mp3`
- 多个会议：`录音2026-01-09-1.m4a`、`录音2026-01-09-2.wav`

**逐字稿文件**（工具生成）：
- 格式：`录音文件名_原文.md`
- 示例：`录音2026-01-09-1_原文.md`

**会议纪要文件**（AI 生成）：
- 格式：`会议纪要YYYY-MM-DD-N.md`（序号与录音/逐字稿一致）
- 示例：`会议纪要2026-01-09-1.md`、`会议纪要2026-01-09-2.md`

**处理流程**：
```
~/Downloads/                                   源文件夹
├── 录音2026-01-09-1.m4a                      原始录音
├── 录音2026-01-09-1_原文.md                   原始逐字稿
         ↓
~/Downloads/2026-01-09/                        脚本创建日期文件夹
├── 录音2026-01-09-1.m4a                      复制录音
├── 逐字稿2026-01-09-1.md                      重命名逐字稿
         ↓
/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/2026-01-09/  自动归档
├── 录音2026-01-09-1.m4a
├── 逐字稿2026-01-09-1.md
└── 会议纪要2026-01-09-1.md                    AI 生成
```

## 配置

### 创建配置文件

运行以下命令创建默认配置文件：
```bash
python3 ~/.claude/skills/meeting/scripts/process_meetings.py --create-config
```

默认配置文件位置：`~/.claude/skills/meeting/config.json`

### 配置选项

```json
{
  "archive_dir": "/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/",
  "overwrite": false,
  "skip_existing": true
}
```

**配置说明**：
- `archive_dir`: 归档目录路径
- `overwrite`: 是否覆盖已存在文件（默认：false）
- `skip_existing`: 是否跳过已存在文件（默认：true）

**会议纪要模板**（AI 生成时使用）：
```
~/.claude/skills/meeting/会议纪要生成.md
```

## 故障排除

**脚本执行失败**：
```bash
# 检查Python版本
python3 --version

# 确认脚本路径
ls -la ~/.claude/skills/meeting/scripts/process_meetings.py

# 添加执行权限
chmod +x ~/.claude/skills/meeting/scripts/process_meetings.py
```

**找不到录音文件**：
- 确保文件名以"录音"开头
- 确保文件扩展名是支持的音频格式：`.m4a`, `.mp3`, `.wav`, `.aac`, `.ogg`, `.flac`, `.wma`
- 正确：`录音2026-01-09-1.m4a` ✅、`录音2026-01-09-2.mp3` ✅
- 错误：`recording-2026-01-09.m4a` ❌（没有中文前缀）
- 错误：`录音2026-01-09-1.txt` ❌（不支持的格式）

**找不到逐字稿**：
- 确保格式为 `录音文件名_原文.md`
- 正确：`录音2026-01-09-1_原文.md` ✅
- 错误：`逐字稿2026-01-09-1.md` ❌

**无法提取日期**：
- 确保录音文件名包含 `YYYY-MM-DD` 格式
- 确保日期有效（如 2026-13-32 会被拒绝）
- 正确：`录音2026-01-09-1.m4a` ✅
- 错误：`recording-2026-01-09.m4a` ❌
- 错误：`录音2026-99-99.m4a` ❌（无效日期）

**归档目录不存在**：
- 脚本会自动创建归档目录
- 确保有足够的权限访问归档位置

**文件已存在**：
- 默认跳过已存在文件，不会覆盖
- 如需覆盖，修改配置文件中的 `overwrite` 选项

## 性能说明

- **小批量**（<10个文件）：即时处理
- **中批量**（10-50个文件）：几秒到几十秒
- **大批量**（>50个文件）：建议分批处理或使用 --no-archive 选项

## 安全特性

✅ **文件保护**：默认不覆盖已存在文件
✅ **日期验证**：自动拒绝无效日期
✅ **错误处理**：详细的错误信息和恢复建议
✅ **交互确认**：重要操作前询问用户确认
