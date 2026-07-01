---
name: health-evening-close
version: 2.0.0
description: "健康每日晚间收口。由调度系统每天 21:30 调用。静默执行：写 Base 完成率/饮食合规度，补填缺失卡路里，写本地 daily-log.md 日总结。不向用户发送消息。"
---

# Health Evening Close（每日晚间收口）

## 触发

- **定时**：由调度系统每天 21:30 调用
- **静默执行**：不向用户发消息，技能完成自己的 task 即可

## 工作流程

```
1. 读取当日记录
   python3 health-system/scripts/health_analytics.py --apply-evening
   （计算运动完成率、饮食合规度）

2. 卡路里补填检查（重要）
   检查当日每个有餐次文本但卡路里为空的字段 → 自动估算补填
   python3 health-system/scripts/health_analytics.py --fill-calories

3. 确定性写入 Base（脚本执行）
   - 运动完成率_%：有训练主题且已记录运动 → 100%，否则 → 0%
   - 饮食合规度：脚本规则推断（优/良/一般/差）
   （AI 可在脚本基础上润色饮食合规度评级）

4. 写入本地 daily-log.md
   路径：~/SynologyDrive/Sync/OS/Health_OS/content/YYYY/MM/daily-log.md
   追加今日完整日志（见格式）

5. 若 suggest_tomorrow_downgrade=true：
   upsert 明日训练强度=减量（仅当明日尚无记录时）
```

## daily-log.md 追加格式

```markdown
---

## YYYY-MM-DD

**体重**: Xkg | **睡眠**: 就寝 HH:MM · 起床 HH:MM · 共 X.Xh

**饮食**
- 早餐：...（约 XXXkcal）
- 午餐：...（约 XXXkcal）
- 晚餐：...（约 XXXkcal）
- 加餐：...（约 XXXkcal）（若有）
- 全日约：XXXXkcal | 合规度：优/良/一般/差

**运动**
- HH:MM | 类型 | 内容 | 时长Xmin
（无运动则写：无）

**备注**: （身体状态/当日情境，若有）
```

## 卡路里补填逻辑

每晚检查：有餐次文本但对应卡路里为空 → 基于文本估算后写入：

```python
for meal in ['早餐', '午餐', '晚餐', '加餐']:
    if record.get(meal) and not record.get(f'{meal}_卡路里'):
        estimated = estimate_calories_from_text(record[meal])
        upsert_by_date(date, {f'{meal}_卡路里': estimated})
```

## 饮食合规度评级规则

| 评级 | 条件 |
|------|------|
| 优 | 全日卡路里在目标区间，无高升糖，三餐记录完整 |
| 良 | 有 1 次高升糖 或 卡路里略超（<10%），但整体结构合理 |
| 一般 | 有 2 次高升糖 或 卡路里超 10–20%，或缺失某餐记录 |
| 差 | 高升糖 ≥3 次，或卡路里超 20% 以上，或完全无记录 |

## 明日降级规则

当 `suggest_tomorrow_downgrade=true` 时（RPE 过高 / 连续无休息 / 安全标记）：

```python
from datetime import datetime, timedelta
from health_base import find_record_by_date, upsert_by_date
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
if not find_record_by_date(tomorrow):
    upsert_by_date(tomorrow, {'训练强度': '减量'})
```

## 写入字段汇总

| 字段 | 来源 |
|------|------|
| 运动完成率_% | 脚本计算 |
| 饮食合规度 | 脚本推断（AI 可润色） |
| 早/午/晚/加餐_卡路里 | 补填（若缺失） |

> 不向用户发消息。本技能只完成数据写入任务。

## 配置引用

`references/config.md`。日结路径见其中「读什么文件」表。
