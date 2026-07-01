---
name: health-weekly-review
version: 2.1.0
description: "健康周反馈。由调度系统每周日 19:00 调用，或用户说「本周健康小结」时触发。汇总本周数据（本地），写入 weekly-review.md 和 profile-updates.md，飞书发摘要（只发不读）。"
---

# Health Weekly Review（周健康反馈）

## 触发

- **定时**：由调度系统每周日 19:00 调用
- **手动**：用户说「本周健康小结」「周健康反馈」

## 数据原则

**只读本地，飞书只发。** 本周数据从脚本与本地 `content/`、`state/` 获取；**禁止**从飞书文档/Base 回读。飞书消息仅为用户通知渠道。

## 工作流程

```
1. 读取本周分析上下文（本地）
   python3 health-system/scripts/health_analytics.py --weekly-review
   content/profile.md、content/{YYYY}/{MM}/monthly-plan.md（如需对照月目标）

2. AI 生成周反馈内容（见格式规范）

3. 写入本地 weekly-review.md（追加）
   路径：content/{YYYY}/{MM}/weekly-review.md

4. 写入本地 profile-updates.md（只记客观信号）
   路径：content/{YYYY}/{MM}/profile-updates.md

5. 飞书发送摘要（≤12 行，仅输出），末尾询问：
   「确认下周继续当前训练计划？（是 / 有调整）」
```

## weekly-review.md 追加格式

```markdown
---

## W27（07.01–07.06）

运动：N/7天完成（完成率XX%）
- 类别分布：有氧X天、上肢X天、下肢X天、核心X天
- 计划完成度：X/Y 天完成
- 主要障碍：（若有）

体重：X → Ykg（↑/↓Δ）
分析：（归因——外食/聚餐/出差/疲劳等具体场景）

饮食：
- 高升糖 X/7天，主要场景：外食X次、在家X次
- 待改进：（具体1项）

亮点：（本周做得好的一项）

下周调整：（具体1-2项）
```

## profile-updates.md 追加格式（只记客观信号）

```markdown
## 2026-WXX 健康观察

- 运动完成：N/7天（按 current-week.json 计划时段统计）
- 高升糖：N次（外食午餐N次、聚餐N次、在家N次）
- 体重变化：X → Ykg
- 睡眠：平均就寝 HH:MM，起床 HH:MM
- 特殊信号：（用户提到的，原词不改写）
- 偏离计划：（若有，说明原因）
```

> **只记录客观信号，不加解读。**「3次高升糖」不是「高升糖率偏高需改善」。

## 飞书消息格式示例

```
📊 本周健康小结（W27）

运动：5/7 天完成 ✅（上周 3/7，进步！）
体重：74.2 → 73.8kg ↓0.4
分析：外食减少，家中做饭比例提升
亮点：晚间运动连续 4 天完成
待改进：早餐两次高升糖（包子/白粥）→ 下周换成鸡蛋+燕麦

下周建议：保持节奏，早餐换蛋白质优先
确认下周继续当前训练计划？（是 / 有调整）
```

## 与周计划的关系

- 用户确认「是」→ 周一 `health-weekly-plan` 按常规模板排计划
- 用户说「有调整」→ 收集变更，周一排计划时纳入

## 配置引用

`references/config.md`
