# 检查与更新命令参考

按 `type` + `check_method` 索引。所有「查最新版」命令均为**只读、可并行**。更新命令需用户确认后才执行。

---

## cli / npm

npm 全局安装的 CLI。

**查最新版**：
```bash
npm view <package> version
```

**查当前版**：
```bash
<cli> --version
# 或（更可靠，直接读安装版本）
npm ls -g <package> 2>/dev/null | grep <package>
```

**更新**——若装在 `/usr/local/lib/node_modules`（如 lark-cli）需 sudo，让用户手动跑：
```bash
sudo npm install -g <package>@latest
```
若装在用户目录（`~/.npm-global` 等）则无需 sudo：
```bash
npm install -g <package>@latest
```

判断是否需 sudo：`which <cli>` 指向 `/usr/local/...` → 需要；指向 `~/.local/...` 或 `~/.npm-global/...` → 不需要。

**例子**：`@larksuite/cli`（lark-cli）

---

## cli / brew

Homebrew 安装。

**查过期**（同时给出当前和最新，无输出 = 已最新）：
```bash
brew outdated --verbose | grep -i <package>
```

或只查最新版：
```bash
brew info <package> 2>/dev/null | head -1
```

**更新**：
```bash
brew upgrade <package>
```

**例子**：`supabase`

---

## cli / github

通过 curl 脚本或手动下载安装、无包管理器的 CLI。

**查最新版**（取最新 release 的 tag，**必须 `-L` 跟随重定向**——仓库迁移会 301）：
```bash
curl -sL https://api.github.com/repos/<owner>/<repo>/releases/latest \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('tag_name','?'))"
```

**查当前版**：
```bash
<cli> --version
```

> 注意版本号格式对齐：GitHub tag 常带 `v` 前缀（如 `v1.15.13`），`<cli> --version` 通常不带。对比时统一去掉 `v` 前缀。

**更新**：重新跑该工具的官方安装脚本。在 skill 里给出官方安装命令（通常在仓库 README），用户确认后执行。

**例子**：`sst/opencode`（opencode，已迁移到 `anomalyco/opencode`，旧 repo 会 301 重定向——靠 `-L` 自动跟随即可，无需手动改 watchlist）

---

## cli / native

工具自带更新检查机制。

**检查 + 更新**（一步）：
```bash
<cli> update
```

**例子**：Claude Code（原生安装器装在 `~/.local/bin`）—— `claude update`。也可用 `npm view @anthropic-ai/claude-code version` 查最新版做对比（Claude Code 同步发 npm）。

---

## plugins（Claude Code 插件）

走 Claude Code `/plugin` marketplace 体系的插件（superpowers、pm-skills、claude-mem、warp 等）。**与 skills CLI 体系（如 lark skills）是两套，别混。**

**检查**：调用封装好的脚本，自动对比所有已装插件 vs 各 marketplace 最新版：
```bash
python3 ~/.claude/skills/tool-update-checker/scripts/check_plugins.py
```

脚本原理（处理 5 种版本声明情况）：
- 读 `~/.claude/plugins/installed_plugins.json`（已装版本 + 所属 marketplace）
- 读各 marketplace 的 `marketplace.json`（最新版本）：marketplace.json 直接声明 version 的（如 superpowers=4.3.1）直接用；version 藏在插件子目录 `plugin.json` 的（`source: "./xxx"`，如 pm-skills、official）去读子目录
- git 类 marketplace（superpowers/pm-skills/thedotmack/warp/axton）：`git fetch` + 读 `origin/HEAD`
- GCS/directory 源（claude-plugins-official、zai-coding-plugins）：非 git，读本地缓存

**已知局限**（脚本已如实标注，不会误报）：
- GCS/directory 源无法 fetch 远程，结果标「用 /plugin 确认」
- installed 版本为 `unknown` 的插件（context7、frontend-design、obsidian-visual-skills）无法精确对比，显示 `?`

**更新**：插件更新优先用 `/plugin` 交互界面（Claude Code 原生，最可靠）。或重新 `/plugin install <plugin>@<marketplace>` 覆盖。更新后重跑脚本确认版本变化。

**卸载/去重**：`/plugin` → uninstall。**注意：部分插件（如 `claude-plugins-official` 来源的）只允许 disable、不能 uninstall**——此时用 disable 即可达去重目的（不再加载、命令不重复），只是文件留在磁盘。对"去掉重复加载"的场景，disable 完全够用，不必纠结无法 uninstall。

---

## skills / marketplace

通过 `skills` CLI 安装、有 lock 记录（`~/.agents/.skill-lock.json`）的 skill。

**检查 + 更新（合一）**——`skills update` 对已是最新版的会自动跳过、不重写：
```bash
npx -y skills update <skill-name-1> <skill-name-2> ... -g -y
```

跑完看输出：`✓ Updated N skill(s)` = 有更新；`Found 0 update(s)` = 全部最新。

**批量更新某来源的全部 skill**（如所有 lark-*）：从 lock 文件提取该前缀的所有 skill 名传入。

> lark skills 的完整更新命令（含 19 个名字）见 memory：`lark-cli-update-method`。

---

## skills / github（手动下载的游离 skill）

游离在 `skills` CLI 管理之外、手动 clone/下载到 `~/.claude/skills/<name>/` 的 skill。**无自动更新机制**，必须靠关注列表登记来源。

**检查**（关注列表需登记 `repo` + `local_path`）：
```bash
# 远程最新 commit（必须 -L 跟随重定向）
curl -sL https://api.github.com/repos/<owner>/<repo>/commits/<branch-or-main> \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['sha'][:10])"

# 本地当前 commit（若 skill 目录是 git clone 的）
git -C <local_path> rev-parse --short HEAD 2>/dev/null

# 若不是 git clone 的，看文件修改时间粗判，或对比本地记录的 commit
```

**更新**：
```bash
# git clone 的情况
cd <local_path> && git pull

# 手动下载的情况：从 source 重新下载覆盖
```

**根本建议**：能迁移就迁移——改用 `npx skills add <owner/repo> -s <skill>` 纳入 `skills` 体系，之后自动可更新，不用再手动查 commit。检查时若发现某 skill 可迁移，顺带提示用户。
