# 健康系统 Base Schema

> 字段 ID 权威来源：`Health_OS/references/system.json` → `base_fields`
> AI 技能**不要**读取字段 ID；写入一律经 `health_base.py`。

## 知识库位置

||| 资源 | 值 |
|------|-----|
| 健康文件夹 | [健康文件夹](https://my.feishu.cn/drive/folder/KF9VfZ3erlhC5SdEqytc3u5Nngh) |
| 文件夹 Token | `KF9VfZ3erlhC5SdEqytc3u5Nngh` |
| Base Token | `C5F9b16P3asODRsiQRscVb0jnZb` |
| 知识空间 ID | `7159811705948635140` |
| 数据表 | `health_records` |
| Table ID | `tblerupODBPxcj7M` |
| 默认视图 | `vewBcexxi1` |
| 旧表（归档） | `tblov8FhUSADcl0J`（体重记录） |
| 健康画像文档 | [健康画像](https://my.feishu.cn/wiki/UvKjwUhDcicOazkhNRqcPOm2nAd) |
| 健康画像 Node | `UvKjwUhDcicOazkhNRqcPOm2nAd` |
| 健康画像 Doc Token | `Uiycd3G1SoOMTxxtvlQc9MSOngg` |
| 健康 Dashboard | [健康 Dashboard](https://my.feishu.cn/wiki/DZ6Dwe2UEirwQjklb3JcrBTHnKh) |
| Dashboard Node | `DZ6Dwe2UEirwQjklb3JcrBTHnKh` |
| Dashboard Doc Token | `QsQ0dttPWoStxGx8hIOcI1LGnKe` |

## 字段 ID 映射

| 字段名 | 字段 ID | 类型 | Upsert Key |
|--------|---------|------|------------|
| 日期 | fld8aMB2Xx | datetime | ✅ 主键 |
| 周次 | fldprMeSL7 | text | |
| 月份 | fldjMOkfqx | text | |
| 体重_kg | fldWyjc7ZG | number | |
| 体脂率_% | fldbzUPjNO | number | |
| 起床时间 | fld0MR0Dmy | datetime | |
| 就寝时间 | fldH2AU7qB | datetime | |
| 睡眠时长_小时 | fldzXicZPV | number | 公式，只读 |
| 早餐 | fld4Yz49jb | text | |
| 早餐_卡路里 | fldYcZcyv1 | number | |
| 午餐 | flda7roZPY | text | |
| 午餐_卡路里 | fldN4EcAxE | number | |
| 晚餐 | fldm6jwhTS | text | |
| 晚餐_卡路里 | fldpBqXOLu | number | |
| 加餐 | fldrjuGgOv | text | |
| 加餐_卡路里 | fldnlGy1G2 | number | |
| 全日卡路里_kcal | fldXUi4fi1 | number | 公式，只读 |
| 饮食合规度 | fld7kFiqCj | select | 晚间补填 |
| 备注 | fldwqLBDMT | text | coach 从用户口述提取；多次追加合并 |
| 运动_1 | fldW8aOVWo | text | |
| 运动_2 | fldozJpkA3 | text | |
| 运动_3 | fldDH2Jjsc | text | |
| 运动类型 | fldJECMVxs | multi-select | 晚间可补填 |
| 运动时长_分钟 | fldvqMo57q | number | 晚间可补填 |
| 运动完成率_% | fldzzUbABD | number | 晚间补填 |
| 身体状态 | fldrXJHXCqw | multi-select | |
| 当日情境 | fldQvOuUnI | multi-select | |
| 训练强度 | fldxHHJtEc | select | **当日运动强度总结**（无/轻度/中等/较高）；晚间补填 |

> **已删除字段**：RPE、精力评分、计划版本、日总结、安全标记、当月文档链接、**训练主题**。
> 周计划主题与时段见本地 `state/current-week.json`；日总结见 `daily-log.md`。
> **Base 写入时机**：用户只口述 → health-coach 写入；晚间收口仅补空。用户不手填任何字段。

## 写入规范

1. 所有写入经 `scripts/health_base.py`，禁止 LLM 直接调用 lark-cli
2. 按日期 upsert：先查后更，只传有值字段
3. 日期格式：`YYYY-MM-DD`（日期字段）/ `YYYY-MM-DD HH:mm`（时间字段）
4. 多选字段传字符串数组：`["上肢力量", "有氧"]`

## 餐次文本格式

```
食物1(份量), 食物2(份量); 标签1,标签2
```

## 运动文本格式

```
HH:MM | 类型 | 内容 | 时长min
```
