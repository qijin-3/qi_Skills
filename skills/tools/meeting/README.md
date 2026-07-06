# 会议纪要整理技能

## 简介

这是一个**全局通用技能**，适用于所有支持标准 skills 目录结构的 AI 编码助手（Goose、Claude Desktop、Aider 等）。

### 安装位置

```
~/.config/agents/skills/meeting-minutes/
```

作为全局技能，它在所有项目中都可用。

## 快速开始

直接告诉 AI 助手：

```
帮我整理会议纪要
```

或

```
处理 /path/to/folder 下的会议录音和逐字稿
```

## 处理流程

### 完整工作流程

1. **扫描与分组**
   - 识别录音文件（.m4a）和逐字稿文件（_原文.md）
   - 提取 ISO 8601 格式的日期和时间戳
   - 按日期分组，识别同一天的多个会议

2. **文件配对**
   - 通过时间戳精确配对录音和逐字稿
   - 验证每个录音都有对应的逐字稿
   - 示例：`recording-2026-01-07T09-00-00-000Z.m4a` ↔ `recording-2026-01-07T09-00-00-000Z_原文.md`

3. **批量重命名**
   - 单个会议：
     - `recording-2026-01-07T12-41-17-251Z.m4a` → `录音2026-01-07.m4a`
     - `recording-2026-01-07T12-41-17-251Z_原文.md` → `逐字稿2026-01-07.md`
   - 多个会议：按时间顺序编号，配对文件使用相同序号
     - 09:00 的会议：`录音2026-01-07-1.m4a` + `逐字稿2026-01-07-1.md`
     - 14:30 的会议：`录音2026-01-07-2.m4a` + `逐字稿2026-01-07-2.md`

4. **生成会议纪要**
   - 读取外部提示词模板（运行时询问路径或使用用户偏好）
   - 逐个处理每个逐字稿，生成对应的会议纪要
   - 会议纪要使用与逐字稿相同的序号
   - 示例：`逐字稿2026-01-07-1.md` → `会议纪要2026-01-07-1.md`

5. **整理归档**
   - 在归档目录创建按日期命名的文件夹（如 `2026-01-07/`）
   - 移动所有相关文件（录音 + 逐字稿 + 会议纪要）到对应文件夹

### 核心原则

⚠️ **文件配对一致性**：录音、逐字稿、会议纪要三者必须使用相同的序号，不能重新编号。

```
正确示例：
录音2026-01-07-1.m4a       ← 序号 1
逐字稿2026-01-07-1.md     ← 序号 1（配对）
会议纪要2026-01-07-1.md   ← 序号 1（配对）
```

## 文件结构

技能包含以下文件：

```
meeting-minutes/
├── SKILL.md              # 技能主文件（必需）
├── README.md             # 本文件
├── EXAMPLES.md           # 详细使用示例
├── FILE_PAIRING.md       # 文件配对逻辑说明
├── PROMPT_TEMPLATE.md    # 提示词模板使用指南
├── template.md           # 会议纪要模板（参考副本）
├── LICENSE.txt           # MIT 许可证
└── scripts/
    └── file_processor.py # 文件处理辅助脚本
```

## 配置

### 归档路径

AI 助手会在运行时询问归档目录，或根据项目上下文推断。

常见选项：
- 当前目录：`./Meeting/`
- 用户指定：任何有效路径

### 会议纪要模板

AI 助手会：
1. 第一次使用时询问模板文件路径
2. 记住该偏好供后续使用
3. 建议常见位置：
   - 项目内：`./prompts/meeting-template.md`
   - 用户目录：`~/Documents/Templates/meeting-template.md`

`template.md` 文件包含模板的参考副本供快速查看。

## 辅助脚本

### file_processor.py

提供以下功能函数：

- `extract_date_from_filename(filename)` - 从文件名提取日期
- `identify_file_type(filename)` - 识别文件类型（录音/逐字稿）
- `generate_new_filename(type, date, index)` - 生成规范文件名
- `generate_rename_mapping(source_dir)` - 生成完整的重命名映射
- `create_date_folders(target_dir, dates)` - 创建日期文件夹

可以独立运行测试：

```bash
python ~/.config/agents/skills/meeting-minutes/scripts/file_processor.py /path/to/files
```

## 注意事项

1. **文件名格式**：依赖 ISO 8601 时间戳格式（如 `2026-01-07T12-41-17-251Z`）
2. **文件类型**：仅支持 .m4a 录音和 .md 逐字稿
3. **目录权限**：确保对归档目录有读写权限
4. **逐字稿质量**：会议纪要质量取决于逐字稿的完整性

## 兼容性

这个技能兼容所有支持标准 skills 目录结构的 AI 编码助手：

- ✅ Goose
- ✅ Claude Desktop
- ✅ Aider
- ✅ 任何支持 Markdown 技能定义的 AI 助手

## 许可证

MIT License - 详见 LICENSE.txt
