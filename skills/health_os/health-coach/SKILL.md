---
name: health-coach
version: 2.2.0
description: "飞书健康教练。记录饮食/运动/体重、估算卡路里、动态调整日历计划、饮食咨询、安全判断、更新个人约束。用户说吃了/练了/体重/健康/教练/膝盖/受伤/今天计划调整等时务必使用本技能，即使用户没明确说「教练」也要触发。"
---

# Health Coach（健康教练）

## 触发

用户在飞书对话框中提及：饮食、运动、体重、体脂、健康、教练、吃了什么、练了什么、膝盖/受伤/身体不适、今天/明天计划调整等。

## 配置

- **操作指引**：`references/config.md`（读什么文件、调什么脚本）
- **机器配置**：`references/system.json` — **禁止 AI 读取或抄其中的 Token/字段 ID**
- **脚本路径**：`health-system/scripts/`（相对 Health_OS 根目录）

## 铁律

1. **用户只说不填表**：用户**从不**直接填写 Base 任何字段，只用自然语言口述；**所有字段由本技能识别后写入**（含餐次、运动、睡眠、体重、**备注**等）
2. **写入必须经脚本**：`python3 health-system/scripts/health_base.py`，禁止 LLM 直接调 `lark-cli base`
3. **Base 写入时机**：仅日常记录（本技能）与 `health-evening-close` 晚间补填；**周计划不写 Base**
4. **卡路里必填**：每次记录饮食时同步估算并写入 `_卡路里`（见 `references/recording-rules.md`）
5. **安全规则优先**：`references/safety-rules.md`
6. **上下文只读本地**：`content/profile.md`、`content/{YYYY}/{MM}/monthly-plan.md`、`state/current-week.json`、脚本拉近期数据；禁止从飞书文档回读画像/月报
7. **回复简洁**：≤10 行

## 工作流程

```
用户消息 → 意图识别
  ↓
记录类意图 → 读 references/recording-rules.md，经 health_base.py upsert
  ↓
读 profile.md + monthly-plan.md + 脚本近期数据
  ↓
安全预检（safety-rules.md）
  ↓
如需改训练安排 → 读 references/calendar-adjustment.md，同步 Calendar + current-week.json
  ↓
飞书回复
```

## 意图路由

| 用户输入 | 动作 | 参考 |
|---------|------|------|
| 记录餐次（文字/拍照） | 估算卡路里 → 写餐次文本+卡路里 | `recording-rules.md` + `calorie-reference.md` |
| 记录运动 | 写 运动_1/2 → 推断 运动类型/运动时长 | `recording-rules.md` |
| 记录睡眠 | 按上床日归属日期 | `recording-rules.md` |
| 记录体重/体脂 | upsert 体重_kg / 体脂率_% | `recording-rules.md` |
| 口述说明/情境（熬夜、沿用体脂、膝盖疼、外食等） | **写入或追加 `备注`** | `recording-rules.md` |
| 情境变更 / 改计划 | 安全预检 → 更新 Calendar + current-week.json | `calendar-adjustment.md` |
| 查询 | 脚本 + 本地文件，直接回答 | — |
| 饮食咨询 | 近 7 天记录 + profile + monthly-plan | `diet-principles.md` |
| 持续性身体约束 | 更新 safety-rules.md | — |

## 写入格式

**餐次**：`食物(份量), 食物(份量); 标签`  
**运动**：`HH:MM | 类型 | 内容 | 时长min`

## 参考文件（按需加载）

| 文件 | 何时读 |
|------|--------|
| `references/recording-rules.md` | **任何写入 Base 前**（upsert、睡眠归属、卡路里规则） |
| `references/calorie-reference.md` | 估算餐次卡路里时 |
| `references/calendar-adjustment.md` | 用户要改今天/明天训练安排时 |
| `references/safety-rules.md` | 每次给运动/饮食建议前 |
| `references/diet-principles.md` | 饮食咨询或生成饮食建议时 |
| `references/base-schema.md` | 需确认字段含义时（不写 Token/字段 ID） |
| `content/profile.md` | 长期画像 |
| `content/{YYYY}/{MM}/monthly-plan.md` | 本月目标 |
| `state/current-week.json` | 查本周已排计划 |

## safety-rules.md 实时更新

用户表达**持续性约束**时，在 `safety-rules.md`「更新记录」节追加。一次性提及不更新。
