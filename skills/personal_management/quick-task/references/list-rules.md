# 清单分类规则

每条任务归入 **一个** 清单。分类后直接创建，不询问用户。

## 决策顺序（从上到下匹配，第一个命中即用）

| 优先级 | 用户意图 | 清单 | 变量 |
|--------|----------|------|------|
| 1 | 想法 / 灵感（尚未决定要不要做） | 💡 Idea | `LIST_IDEA` |
| 2 | 写文章 / 写作 / 自媒体 / 内容 / 脚本 | ✍️ Writing | `LIST_WRITING` |
| 3 | 学习 / 技能 / 效率 / 工具 / 系统 / 自动化 | ♻️ Growing | `LIST_GROWING` |
| 4 | 日常 / 杂务 / 一次性小事 / **不确定放哪** | 🔁 Routine | `LIST_ROUTINE` |

## 特殊规则

**📦 Projects 不归本技能管理。** 用户手动维护 Projects 清单，quick-task **永远不**向 Projects 添加任务。

## 示例

| 用户说 | 清单 | 理由 |
|--------|------|------|
| 「有个想法，AI 能不能帮我选今天穿什么」 | Idea | 纯想法，未决定做 |
| 「写 Personal OS 使用指南」 | Writing | 写作产出 |
| 「研究飞书 Task section API」 | Growing | 技能/系统学习 |
| 「交水电费」 | Routine | 日常杂务 |
| 「帮客户改个 bug」 | Routine | 不确定 → 默认 Routine |
| 「推进好有链接项目」 | Routine | 项目类由用户手动维护 Projects，此处落 Routine |
