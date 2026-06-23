---
name: ai-user-research
description: "AI-powered user research analysis techniques for getting trustworthy, actionable insights. Prevents common AI failures including invented evidence, generic insights, missing contradictions, and weak decision guidance. Use when analyzing user interview transcripts, survey responses, or customer feedback with Claude/ChatGPT/Gemini to ensure insights are verified, nuanced, and actionable."
---

# AI 用户研究

可信赖的 AI 用户研究分析技术。防止幻觉、通用洞察和过度简化的结论。

## 快速开始

**分析面试记录：**

1. 使用[核心提示模板](references/prompt-templates.md#核心提示模板-面试分析)加载上下文
2. 对面试记录运行分析
3. 使用[验证提示词](references/prompt-templates.md#引言验证提示词)验证引言

**分析调查数据：**

1. 在[调查分析模板](references/prompt-templates.md#调查分析提示模板)中指定列和模糊术语
2. 要求区分主题（不要归入通用类别）
3. 单独标记不清晰的响应

## 核心原则

1. **始终验证引言** - AI 会产生引用幻觉；在源记录中验证每条引言
2. **加载特定上下文** - 项目范围、业务目标、产品上下文、参与者细分
3. **拥抱混乱** - 真实研究存在矛盾；不要过度简化
4. **标记不确定性** - 明确报告置信度水平和弱证据
5. **检查矛盾** - 它们比共识更有价值

## 使用哪个 LLM

| 模型 | 最适合 | 权衡 |
|------|--------|------|
| **Claude** | 主要分析 | 不过滤 - 需要验证证据 |
| **Gemini** | 视频分析、严格证据 | 需要提示 2-3 次以获得完整性 |
| **ChatGPT** | 利益相关者沟通 | **最不可靠** - 验证所有内容 |

> 💡 推荐使用 **Claude** 进行分析工作。它在保持基于实际数据的同时覆盖更多内容。

## 常见失败模式

**当 AI 分析感觉不对时**，检查这四种失败模式：

### 1. 虚构证据
AI 生成虚假或"弗兰肯斯坦"引言（从多个来源拼接）。

**解决方案：** 定义引言规则 + 验证每条引言（参见[失败模式 #1](references/failure-modes.md#失败模式-1-虚构证据)）

### 2. 错误或通用洞察
AI 发现适用于任何产品的主题，如"用户想要更好的性能"。

**解决方案：** 加载 4 部分上下文（项目、业务、产品、参与者）以指导解释（参见[失败模式 #2](references/failure-modes.md#失败模式-2-错误或通用洞察)）

### 3. 无法指导决策的"信号"
AI 樱桃挑选证据，在没有细微差别的情况下跳转到自信的推荐。

**解决方案：** 要求证据锚定、矛盾检测和风险标记（参见[失败模式 #3](references/failure-modes.md#失败模式-3-无法指导决策的信号)）

### 4. 矛盾的洞察
AI 平滑处理张力，遗漏面试之间或内部的矛盾。

**解决方案：** 显式矛盾检查 + 用户细分（参见[失败模式 #4](references/failure-modes.md#失败模式-4-矛盾的洞察)）

## 工作流程

### 分析面试

1. **准备上下文** - 使用[核心提示模板](references/prompt-templates.md#核心提示模板-面试分析)
   - 项目范围和决策
   - 业务目标
   - 产品上下文
   - 参与者概述（当前用户、已流失、潜在用户）

2. **运行分析** - 包含引言选择规则和证据锚定要求

3. **验证引言** - 在使用洞察之前运行[验证提示词](references/prompt-templates.md#引言验证提示词)

4. **检查矛盾** - 查看"矛盾和张力"部分

5. **细分洞察** - 寻找用户类型之间的差异

### 分析调查

1. **指定列** - 哪些是客户声音，哪些是元数据
2. **定义模糊术语** - "不值得"在您的上下文中意味着什么
3. **要求区分主题** - 不要将不同的含义归入一起
4. **标记不清晰的响应** - 单独报告模糊的响应

参见[调查分析模板](references/prompt-templates.md#调查分析提示模板)。

### 多模型工作流程（可选）

1. **发现**（Claude）- 综合分析
2. **证据验证**（Gemini）- 验证主题
3. **引言验证** - 始终通过提示词手动验证引言
4. **框架设计**（ChatGPT）- 为利益相关者包装

## 何时使用此技能

在以下情况下使用此技能：
- 使用 AI 分析用户面试记录
- 处理调查响应（CSV 导出）
- 审查 AI 生成的研究洞察
- 诊断 AI 分析为何感觉通用或不可信
- 培训团队可靠的研究实践

## 资源

### [失败模式](references/failure-modes.md)
四种常见 AI 分析失败及其修复方法的详细说明。在诊断问题或设计分析工作流程时阅读。

### [提示模板](references/prompt-templates.md)
即用型提示模板，用于面试分析、调查分析、引言验证和快速参考清单。将它们用作分析的起点。

### [LLM 选择建议](README.md)
如何在 Claude、Gemini 和 ChatGPT 之间选择的指南。阅读本文以决定使用哪个模型。

## 关键参考位置

- **引言规则**：[prompt-templates.md#快速参考-引言选择规则](references/prompt-templates.md#快速参考-引言选择规则)
- **证据锚定**：[prompt-templates.md#快速参考-证据锚定](references/prompt-templates.md#快速参考-证据锚定)
- **矛盾检查**：[prompt-templates.md#快速参考-矛盾检查](references/prompt-templates.md#快速参考-矛盾检查)
- **上下文清单**：[prompt-templates.md#快速参考-上下文加载清单](references/prompt-templates.md#快速参考-上下文加载清单)

## 常见陷阱

❌ **不要** 要求"有力的引言（≤12字）"- 会触发弗兰肯斯坦引言
❌ **不要** 在未验证的情况下接受 AI 引言
❌ **不要** 使用模糊的上下文，如"做研究"
❌ **不要** 让 AI 平滑处理矛盾
❌ **不要** 在没有大量验证的情况下信任 ChatGPT 进行主要分析
❌ **不要** 过度简化复杂的模式

✅ **要** 定义明确的引言选择规则
✅ **要** 在源记录中验证每条引言
✅ **要** 提供 4 部分上下文（项目、业务、产品、参与者）
✅ **要** 要求矛盾检测和风险标记
✅ **要** 尽可能使用 Claude 进行主要分析
✅ **要** 报告细微差别、张力和置信度水平
