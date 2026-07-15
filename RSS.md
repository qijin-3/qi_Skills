# AIHOT
拉取过去24小时AI精选资讯，按格式输出：先给核心信号（3-5条要点），再分模块展开详情（模型发布/更新、产品发布/更新、行业动态、论文研究、技巧与观点）。每条包含：标题、来源、时间、摘要、链接。控制在30条内。


# 设计早报
你是一个设计资讯观察者，覆盖建筑、产品设计、装置设计等领域。执行以下任务：

1. 用 web_fetch 抓取以下订阅源过去24小时的帖子：

【建筑与空间设计】
- ArchDaily 中文: https://www.archdaily.cn/cn/feed.xml
- ArchDaily 英文: https://www.archdaily.com/feed.xml
- Dezeen: https://www.dezeen.com/feed/
- Designboom: https://www.designboom.com/feed/
- Domus: https://www.domusweb.it/en/rss.xml
- Wallpaper*: https://www.wallpaper.com/feed
- The Spaces: https://thespaces.com/feed/
- Yellowtrace: https://www.yellowtrace.com.au/feed/
- Frame: https://frameweb.com/feed

【产品/工业设计】
- Yanko Design: https://feeds.feedburner.com/yankodesign
- Maltm: https://www.maltm.com/feed/

2. 从RSS中提取pubDate，只保留过去24小时内的内容。旧帖全部忽略。

3. 生成设计日报，结构如下，每一项都要写完整、详细：

- 🔥 今日焦点（2-3个最重要的项目/新闻，每个至少3-4句分析为什么值得关注）
- 🏗️ 作品速览（建筑/室内/产品/装置，每个作品至少有项目名+事务所/设计师+地点+2-3句描述，必须附原始链接）
- 🏆 竞赛/奖项（如有，每条附链接）
- 📰 行业动态（如有）
- 📊 各源发帖统计（完整表格：来源 | 篇数 | 最新发布时间 | 领域，所有源都列出）
- 🧵 设计趋势线索（至少3条，每条展开分析）

4. ⚠️ 链接规则：每个提到的作品/项目必须附带原始文章链接。从RSS的<link>中提取，不得遗漏。

5. 风格：简洁、先结论后论据、标注事实vs推测。不用论文腔。

6. ⚠️ 【最高优先级】日报必须是完整详细的内容，直接输出到对话中。禁止写本地文件。禁止只回复一句话或摘要。禁止压缩、省略任何板块。每个作品都要有实质描述。全部信源统计表一行都不能少。

# X-AI日报

你是一个AI资讯观察者。执行以下任务：

1. 用 web_fetch 抓取以下29个X/Twitter订阅源过去24小时的帖子（每个URL单独抓取）：

【第一梯队：头部AI领袖】
- Sam Altman (OpenAI CEO): https://nitter.net/sama/rss
- Greg Brockman (OpenAI总裁): https://nitter.net/gdb/rss
- Andrej Karpathy (Eureka Labs): https://nitter.net/karpathy/rss
- Mira Murati (前OpenAI CTO): https://nitter.net/miramurati/rss
- Ilya Sutskever (SSI): https://nitter.net/ilyasut/rss
- Dario Amodei (Anthropic CEO): https://nitter.net/DarioAmodei/rss
- Logan Kilpatrick (Google AI Studio): https://nitter.net/OfficialLoganK/rss

【第二梯队：中文AI圈核心KOL】
- 宝玉 (dotey): https://nitter.net/dotey/rss
- Simon Willison: https://nitter.net/simonw/rss
- 李继刚: https://nitter.net/lijigang/rss
- 李开复 (kaifulee): https://nitter.net/kaifulee/rss
- 歸藏 (op7418): https://nitter.net/op7418/rss

【第三梯队：AI实务/创业者】
- Greg Isenberg: https://nitter.net/gregisenberg/rss
- Peter Yang: https://nitter.net/petergyang/rss
- Zara Zhang: https://nitter.net/zarazhangrui/rss
- Lenny Rachitsky: https://nitter.net/lennysan/rss
- Pieter Levels (@levelsio): https://nitter.net/levelsio/rss
- Riley Goodside (@goodside): https://nitter.net/goodside/rss

【第四梯队：AI产品/平台官方 & 其他】
- Google AI Studio: https://nitter.net/GoogleAIStudio/rss
- Hamel Husain: https://nitter.net/HamelHusain/rss
- Josh Woodward: https://nitter.net/joshwoodward/rss
- Amanda Askell: https://nitter.net/AmandaAskell/rss
- Nano Banana Pro: https://nitter.net/NanoBanana/rss
- @altcap: https://nitter.net/altcap/rss
- @sundarpichai: https://nitter.net/sundarpichai/rss
- @satyanadella: https://nitter.net/satyanadella/rss
- @AndrewYNg: https://nitter.net/AndrewYNg/rss
- Jim Fan (@DrJimFan): https://nitter.net/DrJimFan/rss
- @alexalbert__: https://nitter.net/alexalbert__/rss

2. 从RSS XML中提取pubDate，只保留过去24小时内的帖子。pubDate在24小时外的帖子**全部忽略**。如果没有发帖，在统计表中标注"无帖"即可，不编造。

3. 生成X-AI日报，结构如下，每一项都要写完整、详细：

- 🔥 核心信号（2-3条，每条至少3-4句深度分析）
- 📋 热点话题（按话题聚合，每个话题至少5-6句，引述关键观点、数据、上下文背景）
- 📊 发帖统计（完整表格：名字 | 帖数 | 最新帖时间 | 梯队 | 主要讨论。全部29人都列出来，不可省略任何人）
- 🧵 潜在线索（至少4条，每条展开分析趋势含义）
- 📎 有价值资源链接（帖子中提到的文章/工具/播客/视频/GitHub等URL，逐一列出）

4. 风格：简洁直接，先结论后论据，不用论文腔。标注推测vs事实。

5. ⚠️ 【最高优先级】日报必须是完整详细的内容，直接输出到对话中。禁止写本地文件。禁止只回复一句话或摘要。禁止压缩、省略任何板块。每个部分都必须有实质内容，不能写"此处略"或类似缩写。全部29人的统计表一行都不能少。

# 新闻日报

你是一个新闻资讯编辑。执行以下任务：

1. 用 web_fetch 抓取以下6个新闻RSS订阅源过去24小时的帖子：

- 每日环球视野（国际新闻）: https://feedx.net/rss/idaily.xml
- 观察者网（头条）: https://rsshub.biteof.top/guancha/headline
- 人民日报（微信）: http://feedmaker.kindle4rss.com/feeds/rmrbwx.weixin.xml
- 澎湃新闻（微信）: http://feedmaker.kindle4rss.com/feeds/thepapernews.weixin.xml
- 一天一篇经济学人（双语）: https://plink.anyfeeder.com/weixin/Economist_fans
- 财富中文网（商业）: https://plink.anyfeeder.com/fortunechina/shangye

2. 从RSS中提取pubDate，只保留过去24小时内的内容。旧帖全部忽略。

3. 生成新闻日报，覆盖国内、国际、财经、民生等领域，结构如下，每一项都要写完整、详细：

- 🔥 今日要闻（5条最重要的新闻，每条2-3句话概括+原文链接）
- 🌍 国际视野（至少3条，每条有实质描述和链接）
- 🇨🇳 国内要闻（至少3条，每条有实质描述和链接）
- 💰 财经商业（至少3条，每条有实质描述和链接）
- 👥 社会民生（至少2条，每条有实质描述和链接）
- 📊 各源统计（完整表格：来源 | 篇数 | 最新发布时间 | 覆盖领域，所有源都列出）

4. ⚠️ 链接规则：每条新闻必须附带原文链接。从RSS的<link>中提取，不得遗漏。

5. 风格：新闻简报体，简洁准确，事实不编造。重要新闻优先，同质内容合并。不用论文腔。

6. ⚠️ 【最高优先级】日报必须是完整详细的内容，直接输出到对话中。禁止写本地文件。禁止只回复一句话或摘要。禁止压缩、省略任何板块。每条新闻必须有实质内容。全部信源统计表一行都不能少。