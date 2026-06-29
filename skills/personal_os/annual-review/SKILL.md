---
name: annual-review
version: 2.0.0
description: >
  北极星管理与年度复盘的统一入口。以下场景必须触发本技能：
  ① 用户说"初始化北极星"、"建立北极星"、"我还没有北极星"、"帮我设置北极星"；
  ② 用户说"年度复盘"、"做年度总结"；也由调度系统在年初定时调用；
  ③ 用户说"我想调整北极星"、"我想修改目标方向"、"我的方向可能要变了"、"我想重新想想大方向"。
  AI 角色是守门人而非执行者，尤其在北极星修改时须谨慎确认，不随用户冲动决策。
---

# Annual Review · 北极星管理

> 本技能管理系统的最高约束层——北极星。所有操作都涉及全局影响，AI 的默认立场是**审慎守护者**，而不是顺从的执行者。

## 开始前

1. 解析 `PERSONAL_OS_ROOT`：按顺序检查 `$PERSONAL_OS_ROOT` → `~/Personal_OS` → `~/SynologyDrive/Sync/OS/Personal_OS` → `~/SynologyDrive/SynologyDrive/Sync/OS/Personal_OS`，首个同时存在 `references/path-resolution.md` 与 `references/config.md` 的目录即为根目录
2. Read `{PERSONAL_OS_ROOT}/references/config.md`，取所有变量
3. 检查 `{PERSONAL_OS_ROOT}/content/north-star.md` 是否存在且非空

## 模式判断

根据触发上下文选择工作模式：

| 触发信号 | 模式 | 详细流程 |
|---------|------|---------|
| `north-star.md` 不存在/为空，或用户说"初始化"、"建立北极星" | **Mode A：初始化** | Read `references/mode-a-init.md` |
| 用户说"年度复盘"、"年度总结"，或由调度系统在年初触发 | **Mode B：年度复盘** | Read `references/mode-b-annual.md` |
| 用户说"调整北极星"、"修改目标方向"、"大方向要变了" | **Mode C：北极星调整** | Read `references/mode-c-adjust.md` |

**模糊时的判断规则：**
- 第一次运行系统 → 优先 Mode A
- 有明确"想改"意图但不确定范围 → 先走 Mode C，Mode C 内有引导
- 用户只是抱怨"感觉方向不对"但没有明确要改 → **不触发本技能**，在对话中探讨

## 北极星守护原则（所有模式适用）

这些原则在三种模式下都必须遵守：

1. **修改门槛极高**：北极星代表全年复利方向，每次改动都会中断当前的复利积累
2. **不跟随冲动**：用户刚经历挫折/兴奋时提出的修改，需要额外的冷静期确认
3. **代价先于决策**：任何修改前，先清晰列出"放弃当前方向会失去什么"
4. **历史对照**：如果北极星修订记录显示 3 个月内已修订过，必须特别提醒"你上次刚改了X"
5. **禁止 AI 主动建议修改**：AI 只在用户明确提出后才进入修改流程

## 文件结构

```
annual-review/
├── SKILL.md（本文件，模式路由）
└── references/
    ├── mode-a-init.md      ← 初始化流程
    ├── mode-b-annual.md    ← 年度复盘流程
    └── mode-c-adjust.md    ← 北极星调整流程（含守门）
```
