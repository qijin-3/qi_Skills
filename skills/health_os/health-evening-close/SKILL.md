---
name: health-evening-close
version: 3.1.1
description: "健康每日晚间收口。从本地 daily-log 统一同步飞书 Base，补全衍生字段，定稿 daily-log。向用户发送总结。"
---

# Health Evening Close（每日晚间收口）

## 数据流（2026-07 起）

```
白天 health-coach → daily-log.md（唯一写入源）
                         ↓
本技能 21:30 → 读 daily-log → health_base.py upsert Base → 定稿 daily-log
```

飞书 Base **仅在晚间收口时更新**（用户口述不再实时写 Base）。

## 工作流程

```
1. 读取今日 daily-log 段落
   路径：~/SynologyDrive/Sync/OS/Health_OS/content/YYYY/MM/daily-log.md
   若段落不存在 → 创建空段并记「无用户记录」

2. 从 daily-log 同步 Base（一步 upsert）

   **推荐**（同步 + 补全衍生字段）：
   ```bash
   cd ~/SynologyDrive/Sync/OS/Health_OS
   python3 health-system/scripts/health_analytics.py --evening-close --date YYYY-MM-DD
   ```

   **仅同步**（不含衍生字段补全）：
   ```bash
   cd ~/SynologyDrive/Sync/OS/Health_OS
   python3 health-system/scripts/health_base.py sync-from-daily-log --date YYYY-MM-DD
   ```

   > 注意：子命令是 `sync-from-daily-log --date`，不是 `--sync-from-daily-log` 旗标。

   **回退**（脚本失败时）：解析 daily-log 当日段落，逐字段调用：
   ```bash
   python3 health-system/scripts/health_base.py upsert --date YYYY-MM-DD --fields '{...}'
   ```
   只传有值字段（勿传空值占位）。

   必须同步的字段（来自 daily-log）：
   - 体重_kg、体脂率_%
   - 就寝时间、起床时间、**异常睡眠**（有则写；睡眠时长_小时 为公式只读）
   - 早餐/午餐/晚餐/加餐 文本 + 各 _卡路里
   - 运动_1/2/3
   - 备注

3. 脚本补全衍生字段（仅补空，不覆盖已有值）
   - **月份**（从 `日期` 推导 `YYYY-MM`）
   - 餐次_卡路里（有餐次文本无卡路里时）
   - 运动类型（从运动文本推断）
   - 训练强度（从运动文本时长推断，见下）
   - 运动完成率_%（对照 current-week.json）
   - 饮食合规度

4. 定稿 daily-log 段落
   按 daily-log-format.md「晚间定稿格式」重写当日段（补训练强度、合规度、完成率）

5. 若 suggest_tomorrow_downgrade=true：
   在 daily-log 或 current-week.json 记提示；不写明日 Base
```

## 禁止写入的字段

| 字段 | 原因 |
|------|------|
| ~~运动时长_分钟~~ | **已废弃**；时长只在运动_1/2/3 文本中，禁止 AI 猜总数 |
| 全日卡路里_kcal | Base **公式字段**，自动汇总各餐卡路里，禁止 AI 填写 |
| ~~身体状态~~ | **已移除**；相关内容写入 daily-log **备注**，不同步 Base |
| ~~当日情境~~ | **已移除**；相关内容写入 daily-log **备注**，不同步 Base |
| ~~周次~~ | **已从 Base 删除**；禁止写入或回退 upsert 时附带 |

## 字段语义

| 字段 | 含义 | 来源 |
|------|------|------|
| **训练强度** | 当日运动强度：`无`/`轻度`/`中等`/`较高` | 从运动文本解析时长推断 |
| **备注** | 自由文字汇总 | daily-log `**备注**` 行 → Base |
| 睡眠 | 就寝/起床时间、异常清醒小时 | daily-log `**睡眠**` 行（可与体重同行） → Base `异常睡眠` |

### daily-log 睡眠格式（解析器均支持）

| 格式 | 示例 |
|------|------|
| 单行摘要（定稿常用） | `**体重**: Xkg \| **睡眠**: 就寝 00:00 · 起床 09:00 · 共 7h` |
| 范围简写 | `**睡眠**: 04:00 - 09:00（5h）` |
| 独立行 | `**睡眠**: 就寝 YYYY-MM-DD HH:MM · 起床 YYYY-MM-DD HH:MM` |
| 占位（跳过） | `**睡眠**: --` 或 `就寝 --:-- · 起床 --:--` |

> `睡眠时长_小时` 为 Base 公式字段，由就寝/起床时间自动计算，**禁止**手动写入。`月份` 由脚本从 `日期` 推导写入（`YYYY-MM`），**禁止**在回退 upsert 中手写。

### 训练强度推断（从运动文本时长）

解析 `运动_1/2/3` 或 daily-log 运动行末尾 `时长Xmin`，取**当日运动总时长**：

| 条件 | 值 |
|------|-----|
| 无运动记录 | 无 |
| 总时长 < 20min | 轻度 |
| 20–45min | 中等 |
| ≥45min 或含波比/HIIT 等 | 较高 |

无法解析时长时按「无」或「轻度」保守处理，**禁止**编造独立「运动时长_分钟」字段。

## 睡眠检查

收口前确认：
- 若用户今日或就寝日曾在 daily-log 记过睡眠 → 必须已写入 Base 的 `就寝时间`/`起床时间`
- 若睡眠行含 `异常醒来 X.Xh` → 同步 Base `异常睡眠`（数字，单位小时）
- 若全天无睡眠记录 → daily-log 定稿写 `**睡眠**: 无`，Base 睡眠字段留空

## 运动完成率规则

对照 `state/current-week.json` 当日 `sessions`：
- 有排期且已记录运动（运动_1/2/3 任一有值）→ 100%
- 有排期无记录 → 0%
- 恢复日无强制场次 → 不写入

## 写入字段汇总

| 字段 | 来源 |
|------|------|
| 结构化记录 | daily-log → Base 同步 |
| 月份 | 脚本从 `日期` 推导 `YYYY-MM` |
| 异常睡眠 | daily-log 睡眠行 `异常醒来 X.Xh` → Base（小时） |
| 早/午/晚/加餐_卡路里 | daily-log；缺失时脚本估算补填 |
| 运动类型 | 从运动文本推断 |
| 训练强度 | 从运动文本时长推断 |
| 运动完成率_% | 对照 current-week.json |
| 饮食合规度 | 脚本规则推断 |

> 不向用户发消息。本技能只完成数据写入任务。

## 配置引用

`references/config.md`。日志格式见 `health-coach/references/daily-log-format.md`。
