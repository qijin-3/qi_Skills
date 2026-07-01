# 飞书知识库文档索引

> 动态内容以飞书文档为唯一真相。本地不维护副本，读写均走飞书 API。

## 知识库结构

```
健康文件夹/  (KF9VfZ3erlhC5SdEqytc3u5Nngh)
├── [Base] health_records 数据表
├── 健康画像          ← 个人约束、习惯、目标（教练必读）
├── 健康 Dashboard    ← 对上暴露的摘要（Personal OS 只读）
└── 健康月报 YYYY-MM  ← 月计划 + 周计划 + 周/月反馈（每月新建）
```

## 文档链接

| 文档 | Wiki URL | Doc Token | 维护者 |
|------|----------|-----------|--------|
| 健康画像 | https://my.feishu.cn/wiki/UvKjwUhDcicOazkhNRqcPOm2nAd | `Uiycd3G1SoOMTxxtvlQc9MSOngg` | health-coach / monthly-review |
| 健康 Dashboard | https://my.feishu.cn/wiki/DZ6Dwe2UEirwQjklb3JcrBTHnKh | `QsQ0dttPWoStxGx8hIOcI1LGnKe` | health-evening-close |
| 健康月报 | 每月新建，命名 `健康月报 YYYY-MM` | — | health-weekly-plan / monthly-review |

## 读取方式

```bash
# 读取健康画像
lark-cli docs +fetch --api-version v2 --as user \
  --doc Uiycd3G1SoOMTxxtvlQc9MSOngg --doc-format markdown

# 追加月报章节
lark-cli docs +update --api-version v2 --as user \
  --doc <月报doc_token> --command append --doc-format markdown \
  --content $'## 第 N 周\n...'
```

## 飞书 Base（数据表）

| 资源 | 值 |
|------|-----|
| Base Token | `C5F9b16P3asODRsiQRscVb0jnZb` |
| Table ID | `tblerupODBPxcj7M` |
| 字段定义 | 见同目录 `base-schema.md` |

## 目标与默认时段

| 项目 | 值 |
|------|-----|
| 体重目标 | 72 kg |
| 早餐 | 09:00 |
| 午餐 | 12:00 |
| 晚餐 | 17:30 |
| 主训练 | 19:30 |
| 睡前拉伸 | 22:00 |
