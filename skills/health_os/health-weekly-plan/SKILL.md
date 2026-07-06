---
name: health-weekly-plan
version: 2.4.0
description: "健康周计划。由调度系统每周一 07:00 调用，或用户说「排周健康计划」「本周运动计划」时触发。计划写入本地 state/current-week.json（真相源）+ 飞书 Calendar（用户视图）。不写飞书 Base。"
---

# Health Weekly Plan（周健康计划）

## 触发

- **定时**：由调度系统每周一 07:00 调用
- **手动**：用户说「排周健康计划」「本周运动计划」

## 数据原则

**读本地，写本地 + Calendar。** 排计划前只读 `content/`、`state/` 与脚本分析；**禁止**从飞书回读上周计划或画像。`current-week.json` 是本周计划的唯一真相源；Calendar 同步给用户查看。

## ⚠️ 不写飞书 Base

周计划生成时**禁止**写入或更新飞书 Base 任何字段。Base 仅在晚间收口（health-evening-close 从 daily-log 同步）时更新；白天 health-coach 只写 daily-log。

## 计划 vs 记录 —— 严格区分

| 载体 | 存放内容 | 写入时机 |
|------|---------|---------|
| **`state/current-week.json`** | 每日主题、强度、**各场次时间与动作**（真相源） | 周计划生成时 |
| **飞书 Calendar** | 与 current-week.json 一致的训练事件（用户视图） | 周计划生成时 |
| **飞书 Base** | 每日实际记录（饮食/运动/体重等） | **仅日常记录 + 晚间收口** |

> 🚫 周计划绝不写 Base。已删除字段：`训练主题`。

## 每日主题模板（7 天循环）

| 星期 | 主题 |
|------|------|
| 周一 | 上肢力量 |
| 周二 | 有氧耐力 |
| 周三 | 下肢力量 |
| 周四 | 上肢力量 |
| 周五 | 有氧耐力 |
| 周六 | 全身综合 |
| 周日 | 恢复日 |

## 排期默认（仅周计划生成时使用）

生成 Calendar 事件与 `current-week.json` 时，按 profile 作息习惯安排**具体时刻**；排定后当日所有技能只读已排时间，不再推断锚点。

| 场次 | 默认时刻 | 时长 |
|------|---------|------|
| 晚间主训 | 19:30（周日 21:00） | 30–45min |
| 下午微训 | 15:00（周六 15:30，周日 16:00） | 10–15min（本周酌情） |

## 工作流程

```
1. 读取操作指引 + 脚本分析（本地）
   references/config.md
   python3 health-system/scripts/health_analytics.py --weekly-plan
   content/profile.md、content/{YYYY}/{MM}/monthly-plan.md
   references/safety-rules.md

2. 安全预检 → 确定本周强度

3. 【强制】先删除本周已有日历事件，再按新计划创建
   （Calendar 为用户视图，须与 current-week.json 一致）

4. 写入 state/current-week.json
   记录本周每天的主题、强度、各场次 time/label/content
```

## current-week.json 格式

```json
{
  "week": "2026-W27",
  "generated_at": "2026-07-01T07:00:00+08:00",
  "days": {
    "2026-07-01": {
      "theme": "上肢力量",
      "intensity": "正常",
      "sessions": [
        {
          "time": "19:30",
          "label": "晚间主训",
          "content": "跳绳300，俯卧撑4×15，仰卧起坐4×20"
        }
      ]
    }
  }
}
```

> `sessions` 须与 Calendar 事件一一对应；`daily-remind` 只读此文件呈现今日计划。

## 调整规则

| 条件 | 调整 |
|------|------|
| 上周完成率 < 50% | 晚间主训降时/降组数 |
| 安全标记有异常 | 周一强制恢复 |
| 体重单周升 > 0.5kg | 加强饮食提示 |

## 防重复检查点

- [ ] 查询本周已有 Calendar 事件
- [ ] 删除所有已有事件
- [ ] 验证本周事件数 = 0
- [ ] 写入 current-week.json
- [ ] 创建 Calendar 事件（与 JSON 一致）
- [ ] 验证创建成功

## 配置引用

`references/config.md`。周计划须符合当月 `monthly-plan.md` 中的运动频率与类别目标。
