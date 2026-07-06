# 设备注册表 Schema

路径：`~/Skill Manager/configs/devices.json`（可选）

```json
{
  "version": 1,
  "devices": [
    {
      "id": "macbook-pro",
      "label": "MacBook Pro",
      "hostnames": ["Jins-MacBook-Pro.local", "macbook-pro"]
    },
    {
      "id": "imac",
      "label": "iMac",
      "hostnames": ["Jins-iMac.local"]
    }
  ]
}
```

## 设备识别流程

1. `--device` CLI 参数
2. 环境变量 `SKILL_MANAGER_DEVICE`
3. `~/Skill Manager/.active-device` 文件（GUI 切换后写入）
4. 匹配 `devices.json` 中的 `hostnames`
5. 回退：`sanitize(socket.gethostname())`，自动创建对应配置文件

## 说明

- 每台设备的 `~/Skill Manager` 目录独立，不跨设备同步
- skill-manager 管理器本身位于 `~/.agent/skills/skill-manager`，不在 `Skill Manager/Skills/` 下
- 其他设备的 `.json` 可因 dotfiles 同步存在，但仅当前 hostname 匹配的配置会被使用
