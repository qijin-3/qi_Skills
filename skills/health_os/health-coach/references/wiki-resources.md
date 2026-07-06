# 飞书知识库文档索引

> **本地为真相，飞书为用户视图。** 技能读上下文一律走本地 `content/`、`state/` 与脚本；飞书文档/Base 仅作展示与同步写入目标，**禁止**在周/月计划与复盘中从飞书回读。
>
> **日记录流（2026-07 起）**：白天 health-coach 只写 `daily-log.md`；每晚 health-evening-close 从 daily-log 统一同步 Base。白天不写 Base。

## 知识库结构

```
健康文件夹/  (KF9VfZ3erlhC5SdEqytc3u5Nngh)
├── [Base] health_records 数据表
├── 健康画像          ← profile.md 的飞书镜像（只写不读）
├── 健康 Dashboard    ← 对上暴露的摘要（Personal OS 只读）
└── 健康月报 YYYY-MM  ← 月计划 + 周计划 + 周/月反馈（每月新建）
```

## 文档链接

| 文档 | Wiki URL | Doc Token | 维护者 |
|------|----------|-----------|--------|
| 健康画像 | https://my.feishu.cn/wiki/UvKjwUhDcicOazkhNRqcPOm2nAd | `Uiycd3G1SoOMTxxtvlQc9MSOngg` | monthly-review **写入**（`health_wiki.py --sync-profile`） |
| 健康 Dashboard | https://my.feishu.cn/wiki/DZ6Dwe2UEirwQjklb3JcrBTHnKh | `QsQ0dttPWoStxGx8hIOcI1LGnKe` | health-evening-close **写入** |
| 健康月报 | 每月新建，命名 `健康月报 YYYY-MM` | — | 已废弃；月/周内容见本地 `content/` |

## 同步写入（仅脚本，技能禁止手写 lark-cli）

```bash
# 将本地 profile.md 同步到飞书健康画像（只写不读）
python3 health-system/scripts/health_wiki.py --sync-profile
```

## 飞书 Base（数据表）

| 资源 | 值 |
|------|-----|
| Base Token | `C5F9b16P3asODRsiQRscVb0jnZb` |
| Table ID | `tblerupODBPxcj7M` |
| 字段定义 | 见同目录 `base-schema.md` |

## 本地真相源

| 内容 | 本地路径 |
|------|---------|
| 长期画像 | `content/profile.md` |
| 月目标 | `content/{YYYY}/{MM}/monthly-plan.md` |
| 周计划 | `state/current-week.json` |
| 周复盘 | `content/{YYYY}/{MM}/weekly-review.md` |
| 日日志（白天真相源） | `content/{YYYY}/{MM}/daily-log.md` |
| 结构化落库 | 每晚 `health-evening-close` → `health_base.py` 从 daily-log 同步 Base |
| 近期记录 | `health_analytics.py`（读 Base 或 daily-log，以脚本实现为准） |
