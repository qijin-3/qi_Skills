---
name: health-coach
version: 2.4.0
description: "飞书健康教练。记录饮食/运动/体重/睡眠到本地 daily-log、估算卡路里、动态调整日历计划、饮食咨询、安全判断、更新个人约束。用户说吃了/练了/体重/健康/教练/膝盖/受伤/今天计划调整等时务必使用本技能，即使用户没明确说「教练」也要触发。"
---

# Health Coach（健康教练）

## 触发

用户在飞书对话框中提及：饮食、运动、体重、体脂、睡眠、健康、教练、吃了什么、练了什么、膝盖/受伤/身体不适、今天/明天计划调整等。

## 配置

- **操作指引**：`references/config.md`（读什么文件、调什么脚本）
- **机器配置**：`references/system.json` — **禁止 AI 读取或抄其中的 Token/字段 ID**
- **脚本路径**：`health-system/scripts/`（相对 Health_OS 根目录）

## 铁律

1. **用户只说不填表**：用户只用自然语言口述；**白天所有记录写入本地 daily-log.md**，不写飞书 Base
2. **白天禁止写 Base**：不调用 `health_base.py`；Base 由 `health-evening-close` 每晚从 daily-log 统一同步
3. **卡路里必填**：每次记录饮食时在 daily-log 餐次行写入估算 `_卡路里`（见 `recording-rules.md`）
4. **睡眠必记**：用户提及睡眠/起床时，按就寝日归属写入 daily-log；格式 `就寝 HH:MM · 起床 HH:MM · 共 X.Xh`（可与体重同行，见 `daily-log-format.md`）
5. **安全规则优先**：`references/safety-rules.md`
6. **上下文只读本地**：`content/profile.md`、`content/{YYYY}/{MM}/monthly-plan.md`、`state/current-week.json`、脚本拉近期数据；禁止从飞书文档回读画像/月报
7. **回复简洁**：≤10 行

## 工作流程

```
用户消息 → 意图识别
  ↓
记录类意图 → 读 recording-rules.md + daily-log-format.md
           → 更新 content/{YYYY}/{MM}/daily-log.md 当日段落
  ↓
读 profile.md + monthly-plan.md + 脚本近期数据（只读，不写 Base）
  ↓
安全预检（safety-rules.md）
  ↓
如需改训练安排 → 读 calendar-adjustment.md，同步 Calendar + current-week.json
  ↓
飞书回复
```

## 意图路由

| 用户输入 | 动作 | 参考 |
|---------|------|------|
| 记录餐次（文字/拍照） | 估算卡路里 → 更新 daily-log 饮食节 | `recording-rules.md` + `calorie-reference.md` |
| 记录运动 | 追加运动行（含时长） | `daily-log-format.md` |
| 记录睡眠 | 按就寝日归属 → 写睡眠行（含分段清醒时算 **异常醒来**） | `recording-rules.md` |
| 记录体重/体脂 | 更新 daily-log 体重/体脂行 | `daily-log-format.md` |
| 口述情境（外食、膝盖疼、出差、熬夜等） | 追加写入 **备注**（自由文字，合并去重） | `daily-log-format.md` |
| 情境变更 / 改计划 | 安全预检 → 更新 Calendar + current-week.json | `calendar-adjustment.md` |
| 查询 | 读 daily-log + 脚本 + 本地文件 | — |
| 饮食咨询 | 近 7 天记录 + profile + monthly-plan | `diet-principles.md` |
| 持续性身体约束 | 更新 safety-rules.md | — |

## 写入格式

**餐次**：`食物(份量), 食物(份量); 标签`  
**运动**：`HH:MM | 类型 | 内容 | 时长min`

## 参考文件（按需加载）

| 文件 | 何时读 |
|------|--------|
| `references/daily-log-format.md` | **任何写入 daily-log 前** |
| `references/recording-rules.md` | **任何记录类意图** |
| `references/calorie-reference.md` | 估算餐次卡路里时 |
| `references/calendar-adjustment.md` | 用户要改今天/明天训练安排时 |
| `references/safety-rules.md` | 每次给运动/饮食建议前 |
| `references/diet-principles.md` | 饮食咨询或生成饮食建议时 |
| `references/base-schema.md` | 需确认 Base 字段含义时（晚间收口用，coach 白天不读也可） |
| `content/profile.md` | 长期画像 |
| `content/{YYYY}/{MM}/monthly-plan.md` | 本月目标 |
| `state/current-week.json` | 查本周已排计划 |

## safety-rules.md 实时更新

用户表达**持续性约束**时，在 `safety-rules.md`「更新记录」节追加。一次性提及不更新。
