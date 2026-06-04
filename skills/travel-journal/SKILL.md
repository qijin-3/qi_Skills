---
name: travel-journal
description: >
  游记生成器 - 帮助用户从零开始创建一个基于地图的互动旅行游记网站（静态 HTML，无需服务器）。
  当用户说"创建游记"、"生成旅行日记"、"travel journal"、"旅行网站"、"帮我做游记"、
  "记录我的旅途"、"制作行程地图"时立即触发。
  也支持对已有游记项目进行后期修改（添加行程、更新日记、重跑照片匹配、更换风格）。
  检测到用户目录中有 data/days.json 时自动进入更新模式。
  只要用户提到游记、旅行记录、行程可视化，都应使用此技能。
---

# 游记生成器

## 工作原理

技能基于一个精心设计的**静态 HTML 模板**，将用户提供的行程、日记和照片组合成一个带有交互地图的游记网站。整个项目无需服务器，直接用浏览器打开 `index.html` 即可。

数据流：`用户输入` → `AI 解析/润色` → `JSON 数据文件` → `Python 脚本处理` → `嵌入 HTML`

---

## 启动前：判断模式

在做任何事之前，先判断当前工作目录是否已有游记项目：

```bash
ls data/days.json 2>/dev/null && echo "UPDATE_MODE" || echo "INIT_MODE"
```

- 找到 `data/days.json` → **更新模式**，跳到「更新模式工作流」
- 找不到 → **初始化模式**，从第 1 步开始

---

## 初始化模式（第一次创建）

### 第 1 步：基本信息

询问用户：
1. **游记名称**（例如：川藏游记、北疆环线、东南亚自驾）
2. **输出路径**（默认：`~/Desktop/[游记名称]/`）

创建输出目录，将技能模板复制进去：

```bash
JOURNAL_NAME="用户输入的名称"
OUTPUT_DIR="$HOME/Desktop/$JOURNAL_NAME"
mkdir -p "$OUTPUT_DIR"
cp -r ~/.claude/skills/travel-journal/template/. "$OUTPUT_DIR/"
cd "$OUTPUT_DIR"
```

---

### 第 2 步：选择电影风格

这一步借鉴 cinematic-ui 的方法论：先通过提问了解用户的旅途情绪，再推导出导演/电影参考，最终翻译成 CSS token。

#### 提问流程（每次只问一个）

**提问 A：旅途是什么类型的？**
```
这段旅途，你想用哪种基调来呈现？
a) 史诗公路 —— 辽阔、粗粝、自由
b) 宁静自然 —— 克制、留白、日常诗意  
c) 精神圣地 —— 仪式感、厚重、历史叠加
d) 奇境探险 —— 壮阔自然、敬畏感
e) 城市漫游 —— 轻盈、偶遇、现代感
f) 随便，给我一个惊喜
```

**提问 B：（根据 A 的答案推荐 1-2 位导演）**  
例如用户选 a（史诗公路）→「我想到了文德斯（《公路之王》）和考里斯马基，你更倾向哪种感觉？」  
例如用户选 c（精神圣地）→「贝托鲁奇的《末代皇帝》和塔可夫斯基的《潜行者》都有仪式感，前者更暖、后者更冷」  

**提问 C：颜色倾向暖还是冷？**（若前两步已经能判断则跳过）

#### 推导 CSS token

根据确定的导演/电影风格，参考 `references/cinematic-styles.md` 中的对应预设或即兴生成。生成规则：

- 从电影的**主色调**（摄影基调）推导 `--paper`（前景色）
- 从**阴影/夜景色**推导 `--ink`（背景色）
- 从**标志性道具或光源色**推导 `--blackGold`（强调色）
- 确保 ink 与 paper 的对比度足够可读
- 选一个匹配情绪的地图底图：
  - 暗调史诗 → `cinematic-dark`
  - 温暖自然 → `cinematic-warm`  
  - 留白克制 → `paper-muted`

如果用户说「随便」，直接默认「圣地金红」风格，不需要提问。

#### 应用风格（⚠️ 必须用这个命令，不要自己写脚本）

`scripts/apply-style.py` **已经存在**，里面内置了 6 个预设风格。直接用 `--preset` 参数调用：

```bash
cd "$OUTPUT_DIR"
python3 scripts/apply-style.py --preset "冰雪禅意" --title "游记名称" --title-en "Journal Title"
```

**可用预设名称**（从中选一个，名称必须完全一致）：
- `黄金公路` — 暖金暗棕，史诗公路风
- `冰雪禅意` — 冷白深灰，日式极简
- `大地翠绿` — 翠绿青蓝，自然纪录片
- `圣地金红` — 深黑金调，仪式感（默认风格，**若用户不要改变，才选这个**）
- `浪漫薄紫` — 淡紫米白，法国新浪潮
- `极简黑白` — 纯黑白对比，现代感

如果用户想要完全自定义的风格（非上述预设），才改用 `--style-json`：
```bash
# 先写 JSON 再调用
python3 scripts/apply-style.py --style-json /tmp/custom_style.json --title "游记名称"
```

脚本会一次性更新 `index.html` 中的**全部** CSS 变量（12个，含 body 渐变背景）和 `data/map.json`。绝对不要自己写字符串替换代码——遗漏变量会导致颜色不一致。

apply-style.py 运行后，**必须紧接着运行 embed 脚本**，否则地图底图变更不生效：

```bash
python3 scripts/apply-style.py --preset "冰雪禅意" --title "游记名称"
python3 scripts/embed-travel-data.py   # ← 不能省略
```

---

### 第 3 步：解析行程

请用户粘贴行程文字，格式不限（按天/按地点/流水账皆可）。

**你负责将自然语言行程解析为结构化数据**，生成以下两个文件：

#### `data/days.json` 格式
```json
[
  {
    "date": "YYYY-MM-DD",
    "label": "X月X日",
    "weekday": "星期X",
    "tone": "red",
    "routeLocationIds": ["location-id-1", "location-id-2"],
    "summary": "当天一句话摘要（20-40字）"
  }
]
```

`tone` 字段根据当天的情绪/景观氛围选择：`red`（热烈/出发/到达大城市）、`blue`（平静/湖泊/雨天）、`green`（自然/森林/牧场）、`white`（雪山/寺庙/清晨）、`blackGold`（史诗/垭口/日落）

#### `data/locations.json` 格式
```json
[
  {
    "id": "location-id",
    "name": "地点名称",
    "coordinates": [经度, 纬度],
    "dates": ["YYYY-MM-DD"],
    "diaryExcerpt": "",
    "photos": []
  }
]
```

**坐标由你根据地理知识估算**（[经度, 纬度]）。对知名城市和景点，直接给出准确坐标。对偏僻地点，估算到合理范围内（误差在 20km 以内通常可接受）。

**地点 ID** 使用 kebab-case 英文拼音，如 `chengdu`、`four-girls-mountain`、`lhasa`。

生成后写入对应文件：
```python
import json
with open("data/days.json", "w", encoding="utf-8") as f:
    json.dump(days, f, ensure_ascii=False, indent=2)
with open("data/locations.json", "w", encoding="utf-8") as f:
    json.dump(locations, f, ensure_ascii=False, indent=2)
```

---

### 第 4 步：日记润色

请用户提供原始日记。可以是：
- 按地点写的片段
- 按天写的流水账
- 一整篇文章

**你负责：**
1. 将日记内容拆分并匹配到对应地点
2. 根据第 2 步选择的电影风格进行文字润色
3. 将润色后的内容写入 `locations.json` 每个地点的 `diaryExcerpt` 字段（约 60-120 字/处）
4. 同时更新 `days.json` 中每日的 `summary` 字段（20-40 字/天）

**文字风格指引**（参考 `references/cinematic-styles.md` 对应风格的「文字调性」）：
- 用第一人称叙述
- 保留原始日记的真实细节和情感
- 调整节奏感和句式以匹配电影风格
- 不要过度文艺化，保持真实感

如果用户没有提供日记，保留 `diaryExcerpt` 为空字符串，不要虚构内容。

---

### 第 5 步：照片处理（可选）

询问用户：「你有要放入游记的照片吗？如果有，请提供照片所在的文件夹路径。」

如果用户提供路径：

```bash
PHOTO_DIR="用户提供的路径"

# 第一步：用 match-photos.py 匹配照片到地点
cd "$OUTPUT_DIR"
python3 scripts/match-photos.py --photo-dir "$PHOTO_DIR"

# 第二步：用 optimize-photos.py 生成缩略图
python3 scripts/optimize-photos.py
```

两个脚本都是幂等的，可以安全地重复运行。

---

### 第 6 步：生成最终 HTML

将数据嵌入 HTML：

```bash
cd "$OUTPUT_DIR"
python3 scripts/embed-travel-data.py
```

完成后告知用户：
```
✅ 游记已生成！

打开方式：用浏览器直接打开 index.html（双击或拖入浏览器）

项目位置：[OUTPUT_DIR]
文件结构：
  index.html         ← 直接打开这个
  data/days.json     ← 行程数据
  data/locations.json ← 地点和日记数据
  data/map.json       ← 地图配置
  public/photos/      ← 处理后的照片

后续修改：在这个项目目录里再次运行游记技能，进入更新模式
```

---

## 更新模式（后期修改已有游记）

检测到已有项目后，询问用户要更新什么：

```
检测到已有游记项目。请问你要更新什么？

a) 添加/修改行程（新增天数或地点）
b) 修改某个地点的日记文字
c) 重新匹配照片（整理了新的照片）
d) 更换视觉风格
e) 更新多项内容
```

根据选择执行对应步骤：

- **a（行程）**：重新执行第 3 步，用户提供新增/修改的行程片段，AI 只更新差异部分（合并而非覆盖）
- **b（日记）**：用户指定地点名称，AI 重写该地点的 `diaryExcerpt`，更新 JSON 后重新运行 embed 脚本
- **c（照片）**：用户提供新的照片文件夹，重新执行第 5 步
- **d（风格）**：重新执行第 2 步，更新 CSS 变量和地图样式
- **e（多项）**：按顺序执行多个步骤

每次修改后都要运行 `embed-travel-data.py` 重新生成 HTML。

---

## 重要注意事项

1. **风格必须通过脚本应用**：不要手动替换 CSS 变量，必须生成 `/tmp/style.json` 后调用 `scripts/apply-style.py`。直接字符串替换会遗漏 `body` 渐变背景、`line`、`line_strong` 等衍生变量。
2. **始终验证坐标**：生成坐标后，简单检查是否在合理范围（中国境内：东经 73°-135°，北纬 18°-54°）
3. **地点 ID 唯一性**：同一地点在 `days.json` 的 `routeLocationIds` 中引用的 ID 必须与 `locations.json` 中的 `id` 完全一致
4. **日期一致性**：每个地点的 `dates` 数组要与 `days.json` 中引用该地点的日期吻合
5. **照片匹配依赖 macOS**：`match-photos.py` 使用 macOS 的 `mdls` 命令读取 EXIF 数据，仅在 Mac 上有效
6. **隐私保护**：模板中不包含任何原始作者的个人数据

---

## 参考文件

- `references/cinematic-styles.md` — 6 种电影风格的完整 CSS token 和文字调性指引
- `template/scripts/match-photos.py` — 照片 EXIF 匹配脚本
- `template/scripts/optimize-photos.py` — 照片缩略图生成脚本（macOS sips）
- `template/scripts/embed-travel-data.py` — 将 JSON 数据嵌入 HTML 的脚本
