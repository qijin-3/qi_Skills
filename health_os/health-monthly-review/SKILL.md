---
name: health-monthly-review
version: 2.1.0
description: "健康月复盘。由调度系统每月 1 号 09:00 调用，或用户说「健康月复盘」时触发。展示上月数据 → 必问 4 个目标问题 → 写 monthly-plan.md（本月目标）→ 更新 profile.md 行为模式（长期）→ 同步飞书快照。"
---

# Health Monthly Review（月健康复盘）

## 触发

- **定时**：由调度系统每月 1 号 09:00 调用
- **手动**：用户说「健康月复盘」「本月健康目标」

## 文档分工（重要）

| 写什么 | 写到哪里 | 禁止写什么 |
|--------|---------|-----------|
| 本月体重/运动/饮食目标、阶段重点 | `monthly-plan.md` | — |
| 长期习惯、慢性指标、数据沉淀的行为模式 | `profile.md`「行为模式」等节 | **禁止**本月目标、当前体重、阶段重点 |
| 飞书快照 | 脚本同步 `profile.md` 全文 | 快照与 profile 一致，不含月计划 |

## 工作流程

```
1. python3 health-system/scripts/health_analytics.py --monthly-review
   展示上月数据摘要

2. 【必做】目标共创（4 问，不可跳过）

3. 目标合理性校验

4. 写入 content/{YYYY}/{MM}/monthly-plan.md
   ← 本月目标、阶段重点、守门备注、上月摘要 全部在这里

5. 更新 content/profile.md
   仅更新「行为模式」五维度 + 必要时「作息习惯」长期数据
   禁止写入本月目标/当前体重/当前阶段重点

6. 检查 references/diet-principles.md、training-principles.md

7. python3 health-system/scripts/health_wiki.py --sync-profile
   （禁止手写 lark-cli + Token）
```

## Step 2：目标共创（必做）

展示上月数据后，必问 4 个问题（体重目标、运动频率、饮食重点、特殊安排），详见 `references/config.md`。

答案写入 **下月** `monthly-plan.md` 的「本月目标」「本月阶段重点」节。

## monthly-plan.md 格式

```markdown
# 健康月计划 YYYY-MM

## 本月目标
- 体重：上月末Xkg → 本月目标Ykg
- 运动：每周 ≥ N 天；类别侧重：...
- 饮食重点：...
- 特殊安排：...

## 本月阶段重点
1. ...
2. ...

## 守门备注
...

## 上月数据摘要
（脚本输出）
```

## Step 5：profile.md 更新范围

**只允许**更新以下长期内容（有数据支撑才写）：

| 节 | 内容 | 更新条件 |
|----|------|---------|
| 作息习惯（长期模式） | 起床/训练锚点统计变化 | 连续 ≥3 周新模式 |
| 行为模式 → 运动时间模式 | 完成时段分布 | 同上 |
| 行为模式 → 完成率影响因子 | 外出/聚餐等与完成率关联 | ≥2 次吻合 |
| 行为模式 → 饮食高风险场景 | 高升糖场景 | ≥3 次有记录 |
| 行为模式 → 回避模式 | 某类训练被跳过 | 连续 2+ 周 |
| 行为模式 → 身体信号 | 疼痛/疲劳触发情境 | 有记录即更新 |
| 健康指标 | 新体检/化验结果 | 用户告知 |

**禁止**在 profile.md 出现：`本月目标`、`当前体重`、`当前阶段重点`、`距目标还差 X kg`（这些只在 monthly-plan 或脚本输出里）。

更新格式：
```markdown
### 更新（YYYY-MM）
- [维度]：…（数据依据）
```

## Step 6：references 文件

连续 ≥3 周新高风险饮食场景 → `diet-principles.md` 更新记录
体能/回避模式固化 → `training-principles.md` 更新记录

## 配置引用

`references/config.md`（操作指引）。机器配置见 `system.json`，仅脚本读取。
