---
name: install-travel-journal
description: >
  Travel Journal 安装引导 — 介绍 travel-journal 技能并帮助用户安装。
  当用户询问 "travel-journal"、"游记生成器"、"游记技能"、"如何创建游记"
  或任何与旅行日记、行程记录相关的问题时触发。
  也适用于用户想了解这个技能但尚未安装的场景。
---

# Travel Journal 安装引导

## 触发条件

当用户表达以下意图时使用此技能：
- 询问 travel-journal 是什么
- 想要创建旅行日记或游记
- 寻找游记制作工具
- 询问如何安装 travel-journal

## 工作流程

### 第 1 步：介绍 travel-journal

用简洁的语言向用户介绍：

```
Travel Journal 是一个 AI 辅助的游记生成技能，帮助你：
• 从零创建基于地图的互动旅行游记网站
• 支持多种电影风格的视觉呈现
• 自动匹配照片到地理位置
• 生成静态 HTML，无需服务器，直接用浏览器打开

适合场景：公路旅行、背包旅行、家庭出游等各类旅行记录。
```

### 第 2 步：询问是否安装

明确询问用户：

```
是否要为你安装 travel-journal 技能？

安装后，你只需要：
1. 告诉我你的行程信息
2. 选择喜欢的视觉风格
3. 提供照片（可选）
4. 就能生成一个完整的游记网站

要安装吗？（回复"是"或"安装"继续）
```

### 第 3 步：执行安装

当用户确认安装后，执行以下操作：

1. **创建临时目录克隆仓库**
   ```bash
   TEMP_DIR=$(mktemp -d)
   cd "$TEMP_DIR"
   git clone https://github.com/qijin-3/qi_Skills.git
   ```

2. **链接技能到用户目录**
   ```bash
   SKILL_SRC="$TEMP_DIR/qi_Skills/skills/travel-journal"
   SKILL_DEST="$HOME/.claude/skills/travel-journal"

   # 删除已存在的旧版本（如果是目录）
   if [ -d "$SKILL_DEST" ] && [ ! -L "$SKILL_DEST" ]; then
     rm -rf "$SKILL_DEST"
   fi

   # 创建符号链接
   ln -sfn "$SKILL_SRC" "$SKILL_DEST"
   ```

3. **清理临时文件**
   ```bash
   rm -rf "$TEMP_DIR"
   ```

4. **验证安装**
   ```bash
   if [ -L "$HOME/.claude/skills/travel-journal" ]; then
     echo "✅ travel-journal 已成功安装！"
   else
     echo "❌ 安装失败，请重试"
   fi
   ```

### 第 4 步：引导使用

安装成功后，告知用户如何开始：

```
✅ travel-journal 已安装！

现在你可以开始创建游记了。试着说：
- "创建一个川藏游记"
- "帮我做个旅行日记"
- "生成北疆环线的游记网站"

技能会引导你完成：
1️⃣ 输入行程信息
2️⃣ 选择视觉风格
3️⃣ 添加日记内容
4️⃣ 匹配照片（可选）
5️⃣ 生成最终的 HTML 网站

准备好了就说"创建游记"吧！
```

## 注意事项

- 如果用户已经安装了 travel-journal，提示他们直接使用即可
- 安装过程使用临时目录，不会污染用户的工作空间
- 安装完成后删除临时克隆的仓库

## 故障排除

如果安装失败，可能的原因：
1. `~/.claude/skills/` 目录不存在 → 提示用户先运行 `mkdir -p ~/.claude/skills`
2. 网络问题无法克隆仓库 → 建议用户检查网络连接
3. 权限问题 → 建议用户检查 `~/.claude/` 目录的写权限
