---
name: tool-update-checker
description: 检查 Claude Code 工具链（CLI 软件、插件、agent skills）是否有新版本需要更新。当用户说"检查更新""工具更新""看看什么该更新了""检查 lark/claude code/supabase/opencode 有没有新版""我的 skill 和插件过期了吗""tool update""更新检查"时使用。运行时遍历关注列表，汇总一份「当前 vs 最新」的更新清单并简述变更，用户确认后再逐项更新。
---

# Tool Update Checker

统一检查本地工具链的更新情况：CLI 软件（claude code、opencode、supabase、lark-cli 等）、Claude Code 插件、agent skills。汇总成报告，**用户确认后再更新**——绝不自动更新。

## 核心数据：关注列表

所有要跟踪的工具登记在 `~/.claude/tool-watchlist.json`。**这是唯一的真相来源**——不在列表里的不会被检查。

字段含义和各类型示例见 `templates/watchlist.example.json`（带注释）。

## 执行流程

### 第一步：读取关注列表

读 `~/.claude/tool-watchlist.json`。若不存在，从 `templates/watchlist.example.json` 复制一份，并提示用户按实际情况调整（尤其补全 `package`/`repo` 等字段）。

### 第二步：逐项检查最新版

按每条的 `type` + `check_method` 分发到对应命令。**具体命令见 `references/check-methods.md`**。分类速查：

- `cli` / `npm` — `npm view <pkg> version` 查最新，`<cli> --version` 查当前
- `cli` / `brew` — `brew outdated --verbose` 查过期项
- `cli` / `github` — curl GitHub releases API 查最新 tag
- `cli` / `native` — 工具自带更新检查（如 `claude update`）
- `plugins` — 跑 `scripts/check_plugins.py`，自动对比所有已装插件 vs marketplace 最新版（处理 5 种版本声明情况）
- `skills` / `marketplace` — `npx skills update <names> -g`（自动跳过最新版，检查与更新合一）
- `skills` / `github` — 关注列表登记 `repo`，对比最新 commit hash（用于手动下载的游离 skill）

**并行检查**：每项检查相互独立，用并行 Bash 调用加速。只读命令可安全并行。

### 第三步：汇总报告

输出一张表，只列「有差异」或全部（视数量）：

| 工具 | 类型 | 当前 | 最新 | 状态 | 备注 |
|------|------|------|------|------|------|

对「需更新」的项，附一行简述：版本号差异 + 变更来源链接（GitHub releases / changelog），让用户能快速看更新了什么。

### 第四步：等待用户确认

**不要自动更新。** 列出可更新的项，问用户：「要更新哪些？」（可多选 / `all` / 具体名字）。默认不更新。

### 第五步：执行更新

按用户选择调用对应更新命令（见 `references/check-methods.md`）。注意：

- **需 sudo 的**（如装在 `/usr/local` 的 npm 全局包 lark-cli）：提示用户用 `! sudo <cmd>` 手动执行，**不要**尝试非交互 sudo（会卡死）。给出可直接复制的命令。
- **插件更新**：优先指引用 `/plugin` 交互界面。
- **更新后**重新跑一次该工具的版本命令，确认升级成功。

## 维护关注列表（对应"安装时询问"诉求）

当帮用户**新安装**一个 skill / cli / 软件后，主动问一句：「要把 **X** 加入 tool-update-checker 的关注列表吗？」用户同意则按模板字段追加一条到 `~/.claude/tool-watchlist.json`。

> 这是手动维护而非自动 hook——简单、可控、不会误加。符合最小可行设计。

## 边界与提醒

- 这个 skill 是**维护工具**，天花板有限。别过度增强（不要自动 hook、不要做自动定时更新）。保持「读列表 → 检查 → 报告 → 确认 → 更新」的单线流程。
- 对于手动下载、游离在 `skills` CLI 之外的 skill：根本解法是改用 `npx skills add <repo>` 纳入体系（自动可更新），而不是一直靠这个 skill 手动查 commit。检查时若发现某 skill 可迁移，顺带建议用户迁移。
