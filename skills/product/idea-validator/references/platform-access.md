# 平台访问能力 · idea-validator

进入 Step 2 前读取本文件。本文件只处理「当前环境能直连哪些平台、不能直连时怎么降级」，搜索词与各平台命令仍在 `search-strategy.md`。

**原则：** 缺能力就降级并在报告里标注，不要中断验证，也不要向用户推送外部安装或下载链接。

---

## 1. 体检（进入 Step 2 前执行一次）

```bash
agent-reach doctor
```

根据输出记录：哪些社交平台已配置、哪些未配置。然后继续 Step 2，不要停下来等用户操作。

| doctor 结果 | 处理 |
|-------------|------|
| 命令可用，部分平台已配置 | 已配置的走直连；未配置的按第 3 节降级 |
| 命令不存在，或本机没有对应技能 | 需登录的社交平台全部按第 3 节降级；App Store / Play / GitHub / HN / YouTube / 哔哩哔哩仍按 `search-strategy.md` 执行 |

---

## 2. 平台能力表

| 平台 | 适用区域 | 直连条件 | 未直连时 |
|------|---------|----------|----------|
| Reddit / X / 小红书 | 海外 / 国内 | `agent-reach doctor` 显示该平台已配置 | 全网搜索降级（见第 3 节） |
| App Store / Google Play | 通用 | 无需额外配置（iTunes API + 网页阅读） | — |
| GitHub / Hacker News | 技术向 | 无需额外配置（`gh` / Algolia） | GitHub 无 `gh` 时用公开 API + 网页阅读 |
| YouTube / 哔哩哔哩 | 海外 / 国内 | 无需额外配置（网页阅读） | — |

实际搜哪些平台由 Step 1d 的区域判断决定，见 `search-strategy.md`「用户画像区域判断与平台选择」。

---

## 3. 降级（静默，不打断用户）

Reddit / X / 小红书无法直连时，改用全网搜索，并加上站点限定与时间过滤：

```bash
exa search "[竞品名] problems site:reddit.com"
exa search "[产品类别] frustrating"
exa search "site:x.com [竞品名] after:2024-12"
```

各平台更具体的降级命令写在 `search-strategy.md` 对应小节，执行搜索时读那里。

在 HTML 报告的平台覆盖里标注（不要假装直连过）：

```
Reddit：⚠️ 全网搜索替代（直连未配置），结果质量低于直接访问
```

模板侧：降级平台给 `.platform-cell` 加上 `platform-degraded`，status 写「⚠ 全网搜索替代，可信度降低」。未启用平台填 `0`。

---

## 4. 不要做的事

- 不要因为缺直连能力而跳过 Step 2 或降低证据门槛
- 不要在对话里主动推销、安装或粘贴第三方工具的外部下载/文档链接
- 用户若自己问起「怎么补上直连」，指向本机已安装的平台访问技能说明；没有该技能则维持降级，继续验证
