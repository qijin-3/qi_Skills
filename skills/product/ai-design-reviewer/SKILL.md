---
name: ai-design-reviewer
description: AI 功能设计评审工具。基于 8 种核心用户意图框架（Know/Learn, Create, Delegate, Oversee, Monitor, Find/Explore, Play, Connect）评估 AI 产品设计质量。支持两种模式：(1) 截图分析 - 分析 UI 设计截图，评估意图匹配度和反模式；(2) 网址测试 - 访问真实网页，使用 Playwright 模拟用户操作并进行交互式测试。当用户说"评审我的 AI 设计"、"分析这个 AI 功能"、"测试我的 AI 产品"或提供 AI 功能的截图/网址时触发。
license: Complete terms in LICENSE.txt
---

# AI Design Reviewer

基于 8 种核心用户意图框架的 AI 产品设计评审工具。

## Quick Start

选择分析模式：

1. **截图分析模式** - 用户提供 AI 功能的 UI 截图
2. **网址测试模式** - 用户提供可访问的网页 URL

## 模式 1: 截图分析

当用户提供 AI 功能设计的截图时：

使用图像分析工具分析截图，评估：

- 识别用户意图类型（Know/Learn, Create, Delegate, Oversee, Monitor, Find/Explore, Play, Connect）
- 评估 UI 表面与意图的匹配度
- 检测常见反模式（如"聊天框万能"陷阱）
- 检查元意图调优（个性化、主动性、自主性、语气、透明度、风险偏好）
- 安全性和可逆性检查

分析完成后，提供：
1. **意图识别**：该功能主要支持哪些用户意图
2. **匹配度评估**：UI 设计是否匹配意图（Canvas/Queue/Digest/List）
3. **问题清单**：发现的反模式和设计缺陷
4. **改进建议**：具体的设计优化方案

## 模式 2: 网址测试

当用户提供可访问的网页 URL 时：

### Step 1: 初始截图分析

首先访问网址并截图，进行静态分析：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state('networkidle')
    page.screenshot(path='/tmp/ai_design_initial.png', full_page=True)
    browser.close()
```

### Step 2: 交互式测试

使用 Playwright 模拟真实用户操作流程：

```python
# 识别关键交互元素
chat_input = page.locator('input[type="text"], textarea[placeholder*="输入"], textarea[placeholder*="ask"]')
action_buttons = page.locator('button:has-text("发送"), button:has-text("Submit"), button[aria-label*="send"]')
```

测试场景包括：
- 输入模糊查询，观察系统响应方式
- 尝试多轮交互，检查是否支持意图流动
- 触发可变操作，验证是否有安全机制（预览/撤销）
- 检查加载状态和错误处理

### Step 3: 深度评估

基于交互测试结果，参考 [AI Intent Checklist](references/checklist.md) 进行系统性评估。

## 评审框架

### 8 种核心用户意图

| 意图类型 | 用户目标 | 推荐的 UI 表面 | 核心指标 |
|---------|---------|---------------|---------|
| Know/Learn | "我想理解这个" | 结构化答案 + 侧边栏源预览 | 理解速度 |
| Create | "我想创建或改变这个" | 画布优先 + 版本控制 | 迭代增量 |
| Delegate | "帮我做这个" | 步骤预览 + 实时进度面板 | 成功率 |
| Oversee | "让我介入并保持控制" | 统一审查收件箱 + 差异对比 | 审查效率 |
| Monitor | "保持我了解和更新" | 智能摘要 + 可调频率 | 信噪比 |
| Find/Explore | "帮我找到和比较选项" | 多模态输入 + 侧边栏对比 | 时间到结果/候选名单 |
| Play | "娱乐我" | 预设模板 + 结构化会话 | 停留时间 |
| Connect | "被倾听；陪伴" | 对话优先 + 情绪追踪 | 关系信任 |

### 元意图调优维度

- **个性化** ←→ 通用化
- **主动性** ←→ 响应性
- **自主性** ←→ 建议性
- **语气** ←→ 中立性
- **透明度** ←→ 黑盒化
- **风险偏好** ←→ 保守性

### 常见反模式检查

- ❌ 强迫"提示词体操"（常见变换应该是按钮）
- ❌ 没有安全网覆盖内容
- ❌ 无预览的静默更改
- ❌ 静默或不可逆地执行
- ❌ 将"操作"伪装成"聊天回复"
- ❌ 过度承诺"通用代理"能力
- ❌ 倾倒无结构化的长文
- ❌ 盲目自信地犯错
- ❌ 黑盒回复
- ❌ 通知噪音

### 安全性和可逆性

对于所有可变操作，必须提供：
- ✅ Plan Preview（计划预览）
- ✅ Dry Run（模拟运行）
- ✅ Undo/Revert（撤销/还原）
- ✅ Audit Trail（审计日志）

## 评审输出格式

完成评审后，提供结构化报告：

```markdown
## AI 功能设计评审报告

### 📋 基本信息
- **分析对象**: [产品名称/功能描述]
- **分析模式**: [截图分析 / 网址测试]
- **主要意图**: [识别出的核心意图]

### 🎯 意图识别
该功能主要支持以下用户意图：
- [ ] Know/Learn - 知识获取
- [ ] Create - 内容创作
- [ ] Delegate - 任务委托
- [ ] Oversee - 监督审查
- [ ] Monitor - 监控更新
- [ ] Find/Explore - 搜索探索
- [ ] Play - 娱乐
- [ ] Connect - 连接陪伴

### 📊 匹配度评估
| 维度 | 评分 | 说明 |
|-----|------|------|
| UI 表面匹配度 | ⭐⭐⭐☆☆ | 当前使用 [聊天框]，推荐使用 [推荐 UI] |
| 意图清晰度 | ⭐⭐⭐⭐☆ | 用户意图明确 |
| 交互一致性 | ⭐⭐☆☆☆ | 存在意图混合但未明确区分 |

### ⚠️ 发现的问题
1. **[问题类别]**: 具体问题描述
   - 影响: [用户体验影响]
   - 严重程度: [高/中/低]
   - 改进建议: [具体建议]

### ✅ 优秀设计
- [列出做得好的设计点]

### 📌 改进优先级
1. **P0 - 必须修复**
   - [问题 1]
2. **P1 - 建议修复**
   - [问题 2]
3. **P2 - 优化建议**
   - [问题 3]
```

## Reference Files

- **[checklist.md](references/checklist.md)** - AI 功能设计自检清单（完整版）

## Best Practices

- **先识别意图，再评估设计** - 不要过早下结论
- **支持多意图混合** - 真实产品常支持多种意图
- **关注意图流动** - 用户应在单一会话中能无缝切换意图
- **考虑元意图调优** - 不同场景需要不同的 AI 行为配置
- **安全性优先** - 可变操作必须有安全机制
- **具体化建议** - 避免空泛的建议，提供可执行的设计方案
