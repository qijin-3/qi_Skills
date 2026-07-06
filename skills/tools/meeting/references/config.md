# 配置说明

## 配置文件位置

技能目录下的 `config.json`（可从 `config.example.json` 复制）：

```bash
cp config.example.json config.json
```

或通过脚本创建：

```bash
python3 scripts/process_meetings.py --create-config
```

## 配置项

```json
{
  "archive_dir": "/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/",
  "overwrite": false,
  "skip_existing": true
}
```

| 字段 | 说明 |
|------|------|
| `archive_dir` | 归档目录路径，脚本会自动创建 |
| `overwrite` | 是否覆盖已存在文件（默认 `false`） |
| `skip_existing` | 是否跳过已存在文件（默认 `true`） |

## 指定自定义配置

```bash
python3 scripts/process_meetings.py -c /path/to/config.json
```
