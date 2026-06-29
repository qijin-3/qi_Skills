---
name: wechat-doubler
description: macOS 微信双开工具。在 macOS 上创建微信应用的副本来实现双开。当用户说"微信双开"、"开启第二个微信"、"创建微信副本"、"同时登录两个微信"、"WeChat 双开"或类似需求时触发此技能。
---

# WeChat Doubler

## 功能

在 macOS 上创建微信应用的独立副本，实现同时登录两个微信账号。

## 工作原理

通过以下步骤创建独立的微信副本：
1. 复制 `/Applications/WeChat.app` 为 `/Applications/WeChat2.app`
2. 修改副本的 Bundle ID 为 `com.tencent.xinWeChat2`（避免应用冲突）
3. 重新签名应用以确保系统识别为独立应用

## 使用方法

直接执行脚本即可完成所有操作：

```bash
bash ~/.claude/skills/wechat-doubler/scripts/double_wechat.sh
```

脚本会自动：
- 检查原版微信是否存在
- 复制应用并修改配置
- 重新签名
- 提供友好的进度提示

**注意**：如果 `WeChat2.app` 已存在，脚本会提示是否覆盖。

## 结果

操作完成后，用户将在「应用程序」文件夹看到两个微信：
- `WeChat.app` - 原版微信
- `WeChat2.app` - 双开版本

两个应用可以同时运行，登录不同的账号，互不干扰。
