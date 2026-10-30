# 百度热榜新闻解读 · 加工操作指南

**版本**：2026-10-30 最终版（v3，带选题评审、配图、docx、定时任务）
**适用场景**：每天从百度热榜抓取前 50 条，过滤涉政/股市实时行情，按标准选出 10 条，写成 1200～1500 字、3～5 张图、头条风格的 Word 文章。
**目的**：照着这份指南，可以从零复现今天的工作，也可以每天自动运行。

> **配套文档**
> - `NEWS_WRITING_GUIDE.md`：写作规范（写作分身必读）
> - `TOPIC_SELECTION_GUIDE.md`：选题评审规范（选题主编必读）
> - `README_NEWS_CLAUDE.md`：简短使用说明
> - `.claude/commands/news-write.md`：一键流程（Claude Code 斜杠命令）

---

## 目录

1. 一页纸总览
2. 需求与目标
3. 旧代码分析（为什么重写）
4. 环境与前置条件
5. 文件与目录
6. 完整流程（10 步）
7. 规则与标准
8. 数据格式
9. 命令速查
10. 今天的实际经过（时间线）
11. 教训与解决方案（重点）
12. 故障排查表
13. 复现清单（Checklist）
14. 日常运维
15. 当前产物清单
16. 后续可改进
17. 附录（关键词、评分表、Prompt 模板）

---

# 1. 一页纸总览

## 1.1 一句话

**抓 50 条 → 过滤涉政/股市行情 → 从全部合格候选里选 10 条 → 逐条检索写作 → 配 3～5 张图 → 生成头条风格 docx → 双质检 → 按日期存档；每天 5:00 自动运行。**

## 1.2 流程图

```
百度热榜前 50 条
   │  collect_hot50.py
   ▼
原始工作清单（约 50 条：排名/标题/摘要/百度链接）
   │  filter_topics.py（剔除涉政、股市实时行情）
   ▼
全部合格候选（今天 39 条）
   │  选题主编按 TOPIC_SELECTION_GUIDE.md 评审
   ▼
选中 10 条 + 5 条备选（selected.json）
   │  prepare_batch.py 合并原始榜单
   ▼
写作批次清单（selected_full.json）
   │  写作分身：WebSearch + 读原文 + 写作 + 选图
   ▼
每篇：.txt（1200～1500 字）+ .sources.json + .images.json
   │  download_images.py 下载/校验/去重
   ▼
每篇：images_<stamp>/序号/（3～5 张图 + images_manifest.json）
   │  build_docx.py
   ▼
每篇：.docx（标题 22 磅、正文 12 磅、短段、图片、短声明）
   │  check_articles.py + check_docx.py
   ▼
10 篇 PASS + _index.md + 按日期目录存档
```

## 1.3 关键数字（今天）

| 项目 | 数值 | 含义 |
|---|---:|---|
| 抓取 | 51 条 | 百度热榜页面实际条数 |
| 本次取 | 前 50 条 | 按用户要求 |
| 过滤掉 | 11 条 | 涉政 8 条 + 股市实时行情 3 条 |
| 合格候选 | 39 条 | 50 - 11 |
| 选中 | 10 条 | 从 39 条里评审选出，不是取前 10 |
| 备选 | 5 条 | 资料/配图不足时递补 |
| 每篇正文 | 1200～1500 字 | 今天实际 1447～1499 字 |
| 每篇段落 | 4～5 段 | 今天全部 5 段 |
| 每篇图片 | 3～5 张 | 今天合计 42 张 |
| 输出 | 10 篇 docx | 全部 PASS |

## 1.4 关键路径

```
项目根目录：
/public/home/hpc/zhulei/superman/quant/code/news_search_writing

今天的成稿：
news_papers/20261030/20261030_1113_01.docx ～ _10.docx

今天的索引：
news_papers/20261030/_index.md

今天的图片：
news_papers/20261030/images_1115/01 ～ 10

今天的选题：
news_title/baidu_20261030_10-14_selected10.json
news_title/baidu_20261030_10-14_selected10_full.json

定时任务：
crontab: 0 5 * * * .../daily_news_cron.sh
```

---

# 2. 需求与目标

## 2.1 最初需求

用 Python 爬百度热搜前 50 条，把标题和摘要发给火山引擎/硅基流动的智能体，由智能体联网检索并写成“资深新闻主编”风格的文章，按加工日期保存。

改为 **Claude Code 自己检索、自己写**，不经过外部 AI API。

## 2.2 今天的三次调整

| 阶段 | 用户要求 | 结果 |
|---|---|---|
| 第一版 | 先跑前 10 条，1900～2100 字，带参考资料 | 完成 10 篇 txt |
| 第二版 | 去掉涉政/股市实时行情；转 docx；每篇 3～5 张图 | 完成 10 篇带图 docx |
| 第三版 | 头条爆款字数偏长，缩减；参考资料整体删除；每天 5:00 定时 | 改为 1200～1500 字、无参考资料、短声明、cron |
| 第四版 | 10 条应从全部合格候选里“选”，不是“取前 10” | 新增选题评审；从 39 条里选 10 + 5 备选，重做今天 10 篇 |

## 2.3 最终标准

- 每天 10 条，从全部合格候选里选；
- 去掉涉政、股市实时行情；保留财政、金融、公司财报、消费金融；
- 正文 1200～1500 字、4～5 段；
- 每篇 3～5 张相关图片，图下标注来源；
- 正文不出现“参考资料”；来源另存 `_sources.json`；
- 文末只保留一句图片版权声明；
- 输出 `.docx`，按日期存放；
- 每天 5:00 自动运行。

## 2.4 今天的最终产出

10 篇全 PASS，见第 15 节；旧版本备份在 `_v1_long/` 和 `_v2_first10/`。

---

# 3. 旧代码分析（为什么重写）

## 3.1 旧抓取器 `baidu_news_crwal_09.py`

- 用 `requests + BeautifulSoup` 抓 `https://top.baidu.com/board?tab=realtime`；
- 页面实际 51 条，提取 `title` 和 `contents`（摘要）；
- 保存 `news_title/baidu_YYYYMMDD_HH-MM_51.txt`；
- 返回格式：`"标题: XXX|摘要: YYY"`。

**问题**：
- `main()` 里写 `n = 20`，然后 `news_final_list[-n:]`，取的是**最后 20 条**（约第 32～51 名），不是前 20；
- 标题末尾偶尔带“新/热”角标；
- 没有 URL 字段，不利于追溯。

**处理**：新写 `20261030_collect_hot50.py`，取前 N 条，附带百度搜索链接，存 TXT + JSON。

## 3.2 旧写作器

- 最新版 `20251007_..._06.py` 用火山引擎 Ark bot，只把标题传给 bot，**摘要被丢掉**；
- 旧版 `20250507_..._05.py` / `20250412_..._03.py` 有完整 system prompt：约 2000 字、4～5 段、不超过 30 字标题、参考资料、固定免责声明；
- 2025 年 4 月成稿是专业体；2026 年 1 月成稿变成“咱老百姓”大白话体（bot 配置变了，不是代码）。
- 旧代码里有硬编码的 WxPusher token 和 API key；**没有改动**，新流程不用它们。

## 3.3 旧成稿的问题

- 文件名只有 `日期_小时_序号.txt`，事后看不出对应哪条热点；
- 没有索引、没有来源、没有质检；
- 没有配图、没有 docx；
- 没有过滤涉政/股市行情；
- 2000 字以上，头条完读率风险高。

## 3.4 保留与不动的部分

- 旧脚本全部保留，不修改；
- 旧成稿（2025 年 4 月、2026 年 1 月）保留；
- 新流程只新增文件，不覆盖旧代码。

---

# 4. 环境与前置条件

## 4.1 机器与路径

| 项目 | 值 |
|---|---|
| 项目根目录 | `/public/home/hpc/zhulei/superman/quant/code/news_search_writing` |
| Python | `/home/zhulei/anaconda3/bin/python`，3.12.7 |
| Claude CLI | `/home/zhulei/.npm-global/bin/claude`，2.1.236 |
| 系统 | Linux，bash |
| 定时任务 | crontab |

## 4.2 Python 依赖

已安装，无需再装：

- `requests`
- `beautifulsoup4`
- `lxml`
- `python-docx` 1.2.0
- `Pillow` 10.4.0

检查：

```bash
python -c "import requests, bs4, lxml, docx, PIL; print('OK')"
```

> **注意**：按用户全局规则，禁止裸 `pip install` 污染 base 环境；本流程不需要安装新包。

## 4.3 Claude Code CLI

```bash
which claude
# /home/zhulei/.npm-global/bin/claude
claude --version
# 2.1.236 (Claude Code)
```

无交互测试：

```bash
cd /public/home/hpc/zhulei/superman/quant/code/news_search_writing
timeout 90 /home/zhulei/.npm-global/bin/claude -p "只回答两个字：正常" --dangerously-skip-permissions
```

实测返回“正常”。会看到一行 `[claude-code:unrecognized_model]` 警告，
这是当前 deepseek 模型名不被 CLI 识别导致的提示，**不影响运行**。

## 4.4 网络限制

- Claude Code 自带的 **WebFetch 在本机被安全策略拦截**，打不开中文新闻网站；
- 但 **Python requests 可以直接抓网页正文**；
- 所以统一用 `20261030_fetch_page_text.py` 读网页，不要用 WebFetch。

实测：

| 网站 | 结果 |
|---|---|
| 澎湃新闻 | 758 字 |
| 腾讯新闻 | 779 字 |
| 新华网 | 5238 字 |
| 知乎 | 403，失败 |
| 部分地方媒体 | 可能 0 段，换来源 |

## 4.5 cron / flock / timeout

```bash
which crontab   # /usr/bin/crontab
which flock     # /usr/bin/flock
which timeout   # /usr/bin/timeout
```

crontab 里已有很多其他管线，**新增任务前必须备份**：

```bash
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
```

## 4.6 代理与模型警告

crontab 里已有：

```
@reboot sleep 5 && nohup python3 /home/zhulei/.claude/deepseek_proxy.py > /tmp/deepseek_proxy.log 2>&1 &
```

`daily_news_cron.sh` 会预检 `deepseek_proxy.py` 是否在运行；没运行时会尝试拉起。

---

# 5. 文件与目录

## 5.1 脚本清单

| 文件 | 作用 |
|---|---|
| `20261030_collect_hot50.py` | 抓百度热榜前 N 条，存 TXT + JSON |
| `20261030_filter_topics.py` | 剔除涉政/股市行情，保留财经类 |
| `20261030_prepare_batch.py` | 合并选题结果与原始榜单，生成写作批次 |
| `20261030_fetch_page_text.py` | 打开新闻网页、提取正文 |
| `20261030_extract_images.py` | 列出网页候选图片地址 |
| `20261030_download_images.py` | 下载、校验、去重、转 JPEG |
| `20261030_build_docx.py` | 生成头条风格 Word |
| `20261030_check_articles.py` | 检查纯文本 + 生成索引 |
| `20261030_check_docx.py` | 检查 Word 图片数/标题/声明 |
| `daily_news_cron.sh` | 每天 5:00 定时任务入口 |

## 5.2 文档清单

| 文件 | 作用 |
|---|---|
| `NEWS_WRITING_GUIDE.md` | 写作规范（1200～1500 字、无参考资料、短声明、配图、敏感题材） |
| `TOPIC_SELECTION_GUIDE.md` | 选题评审标准（公共价值、可写性、配图、多样性、风险） |
| `README_NEWS_CLAUDE.md` | 简短使用说明 |
| `NEWS_WORKFLOW_OPERATIONS_GUIDE.md` | 本文件，完整复现指南 |
| `.claude/commands/news-write.md` | Claude Code 一键流程 |

## 5.3 输入目录 `news_title/`

今天产生：

```
baidu_20261030_09-43_10.txt/json          # 第一轮前10条快照
baidu_20261030_10-14_50.txt/json          # 第二轮前50条
baidu_20261030_10-14_10_filtered.json     # 第二版“前10条”过滤结果
baidu_20261030_10-14_50_filtered_all.json # 全部39条合格候选
baidu_20261030_10-14_selected10.json      # 选题评审：10条+5备选+理由
baidu_20261030_10-14_selected10_full.json # 合并后的写作批次
```

## 5.4 输出目录 `news_papers/20261030/`

今天最终只保留第三版（选题评审后）的 10 篇：

```
20261030_1113_01.txt/.sources.json/.images.json/.docx
...
20261030_1113_10.txt/.sources.json/.images.json/.docx
images_1115/01 ～ 10/
_index.md
```

## 5.5 备份目录

| 目录 | 内容 |
|---|---|
| `_v1_long/` | 第一版长文（约 2000 字、带参考资料） |
| `_v2_first10/` | 第二版压缩后的“前 10 条”备份 + `_index.md` + `images/` |
| `_v2_first10/old_root/` | 第二版原文件（`20261030_1014_*`）和旧 `images/` |

## 5.6 日志目录

```
logs/cron/news_YYYYMMDD_HHMM.log   # 每次定时任务日志
logs/cron/last_status.txt          # 最近一次退出码
```

---

# 6. 完整流程（10 步）

## 6.1 步骤 1：采集前 50 条

```bash
cd /public/home/hpc/zhulei/superman/quant/code/news_search_writing
python 20261030_collect_hot50.py --limit 50
```

输出：

- `news_title/baidu_YYYYMMDD_HH-MM_50.txt`
- `news_title/baidu_YYYYMMDD_HH-MM_50.json`（含 `rank/title/summary/baidu_url`）
- 终端打印 `run_stamp`（例如 `20261030_1014`）

**检查点**：

- 页面实际 51 条，保存 50 条；
- 标题、摘要非空；
- JSON 里 `items` 有 50 条。

## 6.2 步骤 2：过滤（不要截断）

```bash
python 20261030_filter_topics.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --out news_title/baidu_20261030_10-14_50_filtered_all.json
```

**注意**：**不要加 `--limit 10`**。这里要保留全部合格候选（今天 39 条）。

规则：

- 涉政关键词：全会、公报、中共中央、从严治党、党建、习近平、总书记、政治局、纪委、监委、党史、红军、长征、国民党、第一书记、外交部、国防部、台海、涉台、涉港、涉疆、涉藏、安倍、首相、总统、大选、议会、政府工作报告；
- 股市实时行情：开盘、收盘、低开、高开、涨超、跌超、涨停、跌停、沪指、深证成指、创业板指、科创50、KOSPI、韩股、恒生指数、纳斯达克指数、道琼斯、标普500；
- 财经类保留：养老金、财报、净利、营收、银行、保险、基金、债券、利率、汇率、货币政策、财政、税、贷款、存款、支付、消费金融、融资、市值、股价、投资、理财、钱包；
- 手动剔除：关键词抓不住的边界条目，写在 `MANUAL_EXCLUDE`，必须写清原因。

**检查点**：

- 终端打印“保留 N 条；剔除 M 条”；
- 查看剔除明细，确认没有误删；
- 重点确认财政/金融类没有被误删。

## 6.3 步骤 3：选题评审（不是取前 10）

让 Claude Code 以“选题主编”身份执行：

1. 读 `TOPIC_SELECTION_GUIDE.md`；
2. 读过滤后的**全部** `kept` 候选；
3. 按公共价值 30%、可写性 20%、配图可得性 15%、领域多样性 20%、风险控制 15% 打分；
4. 热度只作加分项；
5. 选 **10 条 + 5 条备选**；
6. 同一事件/人物只选 1 条；至少覆盖 4 个领域；
7. 输出 `news_title/<run_stamp>_selected10.json`，包含 selected/backups/not_selected 和每条理由。

**硬约束**：

- 不选涉政、股市实时行情（已在过滤阶段排除）；
- 不选纯八卦、纯猎奇、低公共价值；
- 未成年人、血腥、隐私题材：除非公共价值高且能克制处理，否则不选或放备选；
- 资料明显不足的放备选。

今天的结果：10 条覆盖 8 个领域；5 条备选。

## 6.4 步骤 4：合并批次

```bash
python 20261030_prepare_batch.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --selection news_title/baidu_20261030_10-14_selected10.json \
  --out news_title/baidu_20261030_10-14_selected10_full.json
```

输出 `kept` 列表，每条含：

```
rank, title, summary, baidu_url, category,
batch_index, score, selection_reason
```

**检查点**：

- `batch_index` 从 1 到 10 连续；
- 10 条与 selected 一致；
- 备选仍在 `selected10.json` 里，不合并。

## 6.5 步骤 5：写作

按每批 5 条派发“写作分身”（Agent 工具，general-purpose）。每个分身：

1. 读 `NEWS_WRITING_GUIDE.md`；
2. 用 WebSearch 做 2～3 次搜索；
3. 用 `20261030_fetch_page_text.py` 读 1～3 篇原文；
4. 写 4～5 段、1200～1500 字；
5. 标题 ≤30 字；
6. 正文不出现“参考资料”；
7. 文末只写：
   ```
   声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。
   ```
8. 保存 `.txt`；
9. 保存 `_sources.json`（2～5 条来源）；
10. 用 `20261030_extract_images.py` 选 5 个图片候选，保存 `.images.json`；
11. 不要自己下载图片，不要生成 docx。

输出示例：

```
news_papers/20261030/20261030_1113_01.txt
news_papers/20261030/20261030_1113_01.sources.json
news_papers/20261030/20261030_1113_01.images.json
```

**如果资料/配图不足**：

- 不要硬写；
- 从 `backups` 按顺序递补；
- 在汇报里说明替换原因。

## 6.6 步骤 6：下载并校验图片

```bash
python 20261030_download_images.py \
  --manifest news_papers/20261030/20261030_1113_01.images.json \
  --outdir news_papers/20261030/images_1115/01 \
  --min-count 3 --max-count 5
```

规则：

- 只从引用过的新闻页面取图；
- 每篇 3～5 张；
- 校验：HTTP 200、10KB～15MB、Pillow 可打开、宽 ≥400、高 ≥250、宽高比 0.4～2.6；
- 内容重复只保留第一张；
- 统一转 JPEG，质量 90；
- 少于 3 张时补候选或换来源；仍不够，考虑用备选替换。

## 6.7 步骤 7：生成 docx

```bash
python 20261030_build_docx.py \
  --txt news_papers/20261030/20261030_1113_01.txt \
  --images news_papers/20261030/images_1115/01/images_manifest.json \
  --out news_papers/20261030/20261030_1113_01.docx \
  --rank 18 \
  --original-title "养老金要崩盘？用三本账穿越认知迷雾"
```

排版：

- A4，上下 2.0cm、左右 2.2cm；
- 标题 22 磅加粗、左对齐；
- 标题下一行灰色小字“全文约 XXXX 字 · 配图 X 张”；
- 正文 12 磅微软雅黑、1.5 倍行距；
- 长段落在 Word 里按句子拆成短段（每段最多约 200 字）；
- 配图居中，横图最大 15.5cm 宽，竖图最高 18cm；
- 图下 9 磅灰色说明，标注来源；
- 文末只放一句短声明，**不放参考资料**；
- 文档属性记录 rank/body_chars/images，供质检。

## 6.8 步骤 8：质检

文本质检：

```bash
python 20261030_check_articles.py \
  --dir news_papers/20261030 \
  --prefix 20261030_1113 \
  --count 10 \
  --worklist news_title/baidu_20261030_10-14_selected10_full.json \
  --index news_papers/20261030/_index.md
```

Word 质检：

```bash
python 20261030_check_docx.py \
  --dir news_papers/20261030 \
  --prefix 20261030_1113 \
  --count 10
```

判定：

| 项目 | 合格 | 警告 | 不合格 |
|---|---|---|---|
| 标题 | ≤30 字 | — | >30 |
| 段落 | 4～5 段 | 3 或 6 段 | 其他 |
| 正文字数 | 1200～1500 | 1100～1200 / 1500～1600 | <1100 或 >1600 |
| 来源 | `_sources.json` ≥2 条 | 1 条 | 0 条 |
| 声明 | 短声明一字不差 | — | 缺失/改动 |
| 图片 | 3～5 张 | — | <3 或 >5 |
| 其他 | 无占位符、无 Markdown | — | 有 |

全部 PASS/WARN 才结束；FAIL 的返工。

## 6.9 步骤 9：生成索引

`check_articles.py --index` 会生成：

```
news_papers/<日期>/_index.md
```

包含：

- 本次序号；
- 榜单排名；
- 原标题；
- 成稿标题；
- txt/docx 文件名；
- 正文字数、段数、来源数；
- PASS/WARN/FAIL。

## 6.10 步骤 10：归档与定时任务

- 旧批次移入 `_v1_long/` / `_v2_first10/`；
- 当前日期目录只保留最终批次；
- `daily_news_cron.sh` 每天 5:00 运行；
- crontab：

```
0 5 * * * /public/home/hpc/zhulei/superman/quant/code/news_search_writing/daily_news_cron.sh
```

---

# 7. 规则与标准

## 7.1 选题规则

详见 `TOPIC_SELECTION_GUIDE.md`。核心：

- 不是过滤后取前 N 条；
- 从全部合格候选里选；
- 公共价值优先，热度只加分；
- 同一事件/人物只选一条；
- 至少 4 个领域；
- 10 条 + 3～5 条备选；
- 每条写清选择理由。

## 7.2 写作规则

详见 `NEWS_WRITING_GUIDE.md`。核心：

- 标题 ≤30 字，第一行就是标题，不写“标题：”；
- 正文 4～5 段，每段 250～350 字，总 1200～1500 字；
- 第一段背景，中间原因/影响，最后评论总结；
- 官方媒体口吻，严肃、专业；
- 不用比喻、排比、拟人、夸张；
- 不用第一人称“我”；
- 不以“当……”开头；
- 不出现“标题/正文/第一段”等标注；
- 不写“此处省略/待补充/XXX”；
- 正文不出现“参考资料”；
- 文末短声明一字不差；
- 事实只来自检索材料，不编数字、人名、引语、判决结果。

## 7.3 配图规则

- 只从文章实际引用过的新闻页面取图；
- 每篇 3～5 张；
- 图片要相关：现场、当事人、产品、文件/公告截图、发布会等；
- 不要 logo、二维码、头像、广告位、网站图标、无关人物；
- 敏感题材避免血腥、遗体、受害者/家属照片；
- 每张图写 caption，注明来源；
- 不确定的写“资料图”。

## 7.4 docx 规则

- 标题 22 磅加粗；
- 正文 12 磅微软雅黑，1.5 倍行距；
- 长段落拆短段，手机上更好读；
- 横图最大 15.5cm 宽，竖图最高 18cm；
- 图下 9 磅灰色说明；
- 文末只有一句短声明；
- 不放参考资料。

## 7.5 敏感题材规则

- 涉政：直接过滤，不写；
- 股市实时行情：直接过滤，不写；
- 财政/金融：保留；
- 未成年人、犯罪、事故：
  - 只用官方通报和主流媒体；
  - 不写血腥细节、不还原过程；
  - 不披露未成年人身份；
  - 不用受害者/家属照片；
  - 标题克制，不猎奇；
  - 重点讨论制度、支持、法律边界。
- 娱乐/社会：不传播未经证实八卦，尊重隐私。

## 7.6 字数依据

公开创作经验（非平台官方硬规则）：

| 内容类型 | 建议字数 |
|---|---:|
| 热点资讯/快讯 | 500～800 |
| 常规图文/观点 | 800～1500 |
| 深度分析/科普 | 1200～2500 |
| 微头条 | 100～500 |

结论：热点解读用 **1200～1500 字**，加上标题、图说、短声明约 1600～1800 字，兼顾信息量和完读率。

---

# 8. 数据格式

## 8.1 采集 JSON

```json
{
  "meta": {
    "collected_at": "2026-10-30 10:14:00",
    "run_stamp": "20261030_1014",
    "source_url": "https://top.baidu.com/board?tab=realtime",
    "total_on_page": 51,
    "saved_count": 50,
    "limit": 50
  },
  "items": [
    {
      "title": "二十届五中全会公报",
      "summary": "中国共产党第二十届中央委员会第五次全体会议……",
      "baidu_url": "https://www.baidu.com/s?wd=...",
      "rank": 1
    }
  ]
}
```

## 8.2 过滤 JSON

```json
{
  "meta": {"kept_count": 39, "excluded_count": 11},
  "kept": [
    {"rank": 3, "title": "...", "summary": "...", "baidu_url": "...", "category": "other", "batch_index": 1}
  ],
  "excluded": [
    {"rank": 1, "title": "二十届五中全会公报", "category": "political", "reason": "涉政关键词：全会"}
  ]
}
```

## 8.3 选题 JSON

```json
{
  "selected": [
    {
      "batch_index": 1,
      "rank": 18,
      "title": "养老金要崩盘？用三本账穿越认知迷雾",
      "category": "finance",
      "score": 9.3,
      "reason": "公共价值最高……"
    }
  ],
  "backups": [
    {"rank": 31, "title": "红果开始给自己踩刹车了", "category": "tech", "score": 7.9, "reason": "..."}
  ],
  "not_selected": [
    {"rank": 5, "title": "西班牙华人女子因赖床错过事故列车", "reason": "与 rank 35 同一事故，去重放弃"}
  ]
}
```

## 8.4 写作批次 JSON

```json
{
  "meta": {"count": 10, "backups": 5},
  "kept": [
    {
      "rank": 18,
      "title": "养老金要崩盘？用三本账穿越认知迷雾",
      "summary": "...",
      "baidu_url": "...",
      "category": "finance",
      "batch_index": 1,
      "score": 9.3,
      "selection_reason": "..."
    }
  ]
}
```

## 8.5 来源 JSON `_sources.json`

```json
{
  "rank": 18,
  "sources": [
    {"title": "“养老金要崩盘”？用“三本账”穿越认知迷雾", "media": "人民日报", "url": "http://opinion-app.people.cn/..."}
  ]
}
```

## 8.6 图片候选 `_images.json`

```json
{
  "rank": 18,
  "images": [
    {
      "url": "https://...",
      "caption": "上海市虹口区市民驿站日间照料中心，老人们参加健康讲座（资料图）",
      "source_page": "https://...",
      "source_name": "新华社"
    }
  ]
}
```

## 8.7 图片最终清单 `images_manifest.json`

```json
{
  "rank": 18,
  "article": "...",
  "images": [
    {
      "local_path": "/.../img_01.jpg",
      "filename": "img_01.jpg",
      "url": "https://...",
      "caption": "...",
      "source_page": "https://...",
      "source_name": "新华社",
      "width": 600,
      "height": 380
    }
  ]
}
```

## 8.8 索引 `_index.md`

```markdown
| 本次序号 | 榜单排名 | 原标题 | 成稿标题 | 文件 | 正文字数 | 段数 | 来源数 | 状态 |
|---|---|---|---|---|---|---|---|---|
| 1 | 18 | 养老金要崩盘？... | 三本账看清养老金... | txt：...；docx：... | 1447 | 5 | 5 | PASS |
```

---

# 9. 命令速查

## 9.1 采集

```bash
python 20261030_collect_hot50.py --limit 50
```

## 9.2 过滤

```bash
python 20261030_filter_topics.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --out news_title/baidu_20261030_10-14_50_filtered_all.json
```

## 9.3 合并批次

```bash
python 20261030_prepare_batch.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --selection news_title/baidu_20261030_10-14_selected10.json \
  --out news_title/baidu_20261030_10-14_selected10_full.json
```

## 9.4 读网页

```bash
python 20261030_fetch_page_text.py "网址1" "网址2" --max-chars 6000
```

## 9.5 提图片

```bash
python 20261030_extract_images.py "网址1" "网址2" --max 12
```

## 9.6 下载图片

```bash
python 20261030_download_images.py \
  --manifest news_papers/20261030/20261030_1113_01.images.json \
  --outdir news_papers/20261030/images_1115/01 \
  --min-count 3 --max-count 5
```

## 9.7 生成 docx

```bash
python 20261030_build_docx.py \
  --txt news_papers/20261030/20261030_1113_01.txt \
  --images news_papers/20261030/images_1115/01/images_manifest.json \
  --out news_papers/20261030/20261030_1113_01.docx \
  --rank 18 --original-title "养老金要崩盘？用三本账穿越认知迷雾"
```

## 9.8 质检

```bash
python 20261030_check_articles.py \
  --dir news_papers/20261030 --prefix 20261030_1113 --count 10 \
  --worklist news_title/baidu_20261030_10-14_selected10_full.json \
  --index news_papers/20261030/_index.md

python 20261030_check_docx.py \
  --dir news_papers/20261030 --prefix 20261030_1113 --count 10
```

## 9.9 定时任务

```bash
# 干跑
DRY_RUN=1 bash daily_news_cron.sh

# 手动跑一次
bash daily_news_cron.sh

# 查看状态
cat logs/cron/last_status.txt
ls -t logs/cron/news_*.log | head -1
```

---

# 10. 今天的实际经过（时间线）

> 时间来自终端输出和日志，精确到分钟，供复盘。

| 时间 | 事件 | 结果 |
|---|---|---|
| 09:43 | 第一轮抓取前 10 条 | 51 条页面，保存 10 条 |
| 09:45～09:56 | 第一版 10 篇（约 2000 字、带参考资料） | 10 篇 txt，全部 PASS |
| 10:14 | 按新要求重新抓前 50 条 | 50 条工作清单 |
| 10:19～10:24 | 第二版第一批 5 篇（带 docx/图） | 5 篇 |
| 10:25～10:31 | 第二版第二批 5 篇 | 10 篇全部 PASS |
| 10:50 | 安装 5:00 cron | 已写入 crontab |
| 10:50～10:53 | 按“1200～1500 字、删参考资料”压缩前 10 篇 | 全部 PASS |
| 11:10 | 选题主编试选 10 条 + 5 备选 | `selected10.json` |
| 11:13 | 按新选题重做：保留 4 条、迁移、写 6 条新选题 | 新批次 `20261030_1113` |
| 11:15～11:20 | 6 条新选题完成、下载图片、生成 docx | 10 篇齐 |
| 11:20 | 最终双质检 | 10/10 PASS |
| 11:20 | 旧批次归档 | `_v2_first10/` |
| 11:21 | cron 干跑验证 | 正常 |

**关键决策**：

1. 不再用旧 API，改 Claude Code 自己写；
2. 去掉涉政/股市行情，保留财经；
3. 字数从 2000 压到 1200～1500；
4. 参考资料移出正文，改存 `_sources.json`；
5. 10 条从 39 条里选，不是取前 10；
6. 图片从新闻原文取，3～5 张，带来源；
7. 每天 5:00 定时，10 条。

---

# 11. 教训与解决方案（重点）

## 11.1 旧代码取数 bug：`[-20:]` 取的是最后 20 条

- **现象**：旧抓取器 `main()` 写 `n=20`，`news_final_list[-n:]`；
- **原因**：列表按排名从高到低，`[-20:]` 取末尾 20 条（约第 32～51 名）；
- **处理**：新采集器明确 `items[:limit]`，取前 N；
- **以后**：任何“前 N”都不要用负索引截取；先打印首尾排名验证。

## 11.2 最新写作器只传标题，摘要丢失

- **现象**：`20251007_..._06.py` 用 `split('|')[0]` 只取标题；
- **原因**：旧代码为适配 bot，丢掉了摘要；
- **处理**：新流程把 `title + summary + baidu_url` 都传给写作分身；
- **以后**：检查输入字段是否完整，别让“省事”丢掉关键信息。

## 11.3 WebFetch 被安全策略拦截

- **现象**：`WebFetch` 对澎湃、腾讯、央广等返回“无法验证域名安全”；
- **原因**：本机安全策略/域名验证限制；
- **处理**：用 Python `requests` 抓网页，`20261030_fetch_page_text.py`；
- **以后**：写作分身明确禁用 WebFetch，统一用脚本；失败就换来源。

## 11.4 图片下载的坑

- **坑 1：最小文件 20KB 太高**：中新网 15～19KB 的图被判“太小”；
  - **处理**：降到 10KB，同时保留宽 ≥400、高 ≥250 的尺寸检查。
- **坑 2：竖图占满整页**：固定 15.5cm 宽，竖图高度可能 22cm；
  - **处理**：docx 里最大高度 18cm，按比例反推宽度。
- **坑 3：重复图**：同一张图不同 URL；
  - **处理**：MD5 去重。
- **坑 4：说明重复来源**：caption 已有“来源：xxx”，builder 又追加“来源：yyy”；
  - **处理**：builder 检查 caption 是否已含“来源：”，有就不追加。
- **坑 5：只抓到 logo/二维码**：
  - **处理**：过滤 URL 关键词 + 尺寸/比例校验；换来源页。
- **坑 6：敏感题材图**：
  - **处理**：只用官方宣传海报/活动资料图，不用受害者/家属照片。

## 11.5 字数/段数的坑

- **现象**：第一版 2000 字，头条完读率风险高；第 7 篇曾写成 10 段、2340 字，FAIL；
- **原因**：写作分身按“深度分析”写，段落拆得太碎/太长；
- **处理**：
  - 统一 1200～1500 字、4～5 段；
  - 第 7 篇合并成 5 段、删到 1450～1499；
  - 质检阈值改为 1200～1500 PASS、1100～1600 WARN；
- **以后**：写作 prompt 明确字数/段数；先跑质检再生成 docx；超了就压缩，不要注水。

## 11.6 子代理卡住

- **现象**：C 罗那条的写作分身卡在“现在我来读取权威报道的正文”，几分钟没落盘；
- **原因**：可能陷入反复搜索/读取循环；
- **处理**：
  - `TaskStop` 停掉；
  - 自己查直播吧 + 新浪体育，按规范写；
  - 补到 1912 字，PASS；
- **以后**：
  - 一条热点一个分身；
  - 给明确时间/工具上限；
  - 超过预期就催一次，仍不动就停掉手工写；
  - 不要让一个分身拖住整批。

## 11.7 文字与 docx 不同步

- **现象**：第 7 篇 docx 用 1471 字版本生成，分身随后又写到 1499 字；
- **原因**：分身在我生成 docx 之后才最终落盘；
- **处理**：等分身正式通知，检查文件时间/字数，重建 docx；最终 1499 字，PASS；
- **以后**：
  - 等所有分身通知完成再批量生成 docx；
  - 生成后核对 txt 字数与 docx 核心属性；
  - 有变化就重建。

## 11.8 选题不是取前 10

- **现象**：第二版用 `--limit 10`，只是过滤后截前 10；
- **原因**：把“每天 10 条”理解成“前 10 条”；
- **处理**：
  - 过滤时不加 `--limit`，保留 39 条；
  - 选题主编按公共价值/可写性/配图/多样性/风险评分；
  - 选 10 + 5 备选；同一事件/人物去重；
  - 今天保留 4 条、新写 6 条、放弃 6 条；
- **以后**：始终“先评审、后写作”；不要把排名当唯一标准。

## 11.9 参考资料的取舍

- **现象**：第一版文末有参考资料，读者阅读被打断，篇幅变长；
- **处理**：
  - 正文和 docx 删除“参考资料”；
  - 来源另存 `_sources.json`，只供内部核对；
  - 图片下仍标来源；
  - 文末只留一句短声明；
- **以后**：发布版干净，内部可追溯；不要把内部审计信息塞进正文。

## 11.10 cron 的坑

- **坑 1：PATH 太短**：cron 里 `python`/`claude` 找不到；
  - **处理**：脚本里 `export PATH=...`，用绝对路径。
- **坑 2：HOME 不对**：Claude 找不到配置；
  - **处理**：`export HOME=/home/zhulei`。
- **坑 3：代理没起来**：`claude` 失败；
  - **处理**：预检 `deepseek_proxy.py`，没运行就拉起。
- **坑 4：权限询问卡住**：无人值守没人点“允许”；
  - **处理**：`--dangerously-skip-permissions`（用户已同意）。
- **坑 5：任务重叠**：
  - **处理**：`flock`。
- **坑 6：任务卡死**：
  - **处理**：`timeout 10800`。
- **坑 7：模型名警告**：
  - **现象**：`[claude-code:unrecognized_model]`；
  - **处理**：不影响运行；实测返回正常；日志里保留即可。
- **坑 8：crontab 覆盖其他任务**：
  - **处理**：先 `crontab -l > backup`，再追加，再 `crontab`。

## 11.11 敏感题材

- **例子**：母亲将 7 岁女儿推下窗台；
- **处理**：
  - 只用裁判文书/官方通报/主流媒体；
  - 不写血腥细节、不还原过程、不披露孩子身份；
  - 标题克制；
  - 配图用最高检/妇联宣传海报、妇联活动资料图；
  - 不用受害者/家属照片；
- **结果**：文章克制、专业，图片 5 张全部合格；
- **选题**：最终评审把它放在不选/备选，避免风险。

## 11.12 备份

- **做过的备份**：
  - `_v1_long/`：第一版长文；
  - `_v2_first10/`：第二版压缩后的前 10 条；
  - `_v2_first10/old_root/`：第二版原文件；
  - `/tmp/crontab_backup_*.txt`：crontab 备份；
- **以后**：任何“重做/覆盖/删除”前，先复制到带日期的备份目录；备份要包含 txt/docx/sources/images/index。

## 11.13 事实核对

今天抽查过的例子：

- 银行误存案：区分“调解”与“判决”，不能把调解写成判决；
- 西班牙高铁：69 人遇难官方口径；160～200 公里是报告估计；追尾是碰撞方式，脱轨是后果；
- 谷歌：Q3 云收入 307.1 亿美元、资本开支 513.6 亿美元、自由现金流 -90.65 亿美元；
- 养老金：10.76 亿参保、2025 年三项社保基金收入 9.1 万亿/支出 8.1 万亿/结余 10.2 万亿、60 岁以上 3.23 亿；
- 张雪机车：25163 台销量、1.5 亿元融资、110 余件商标、23 项专利；
- 从严治党：18444.3 元、1462 户、857 人、1719.29 万元等，全部回查人民日报原文。

**规则**：数字、人名、引语、判决结果，必须能在检索材料里找到；不同来源冲突时说明差异，优先官方口径。

---

# 12. 故障排查表

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 采集到 0 条 | 页面结构变了/被反爬 | 检查 UA/Referer；看类名前缀；手动打开页面 |
| 采集到 51 条但只保存 10 | 加了 `--limit 10` | 想要全部候选就不要加 limit |
| 过滤后只剩几条 | 关键词太宽 | 看剔除明细；调整 `MANUAL_EXCLUDE`/关键词 |
| 选题还是前 10 条 | 没做选题评审/直接用了 limit | 按 `TOPIC_SELECTION_GUIDE.md` 重选 |
| WebFetch 打不开 | 安全策略拦截 | 用 `20261030_fetch_page_text.py` |
| 图片只有 0～2 张 | 候选不足/尺寸太小/被反爬 | 换来源页；补候选；检查 Referer；放宽到 3 张以下就换备选 |
| 图片显示过大 | 竖图固定宽度 | 检查 builder 的最大高度 18cm |
| 图片说明重复来源 | caption 已有来源 | builder 检查“来源：” |
| 正文字数超 1500 | 写多了 | 删重复铺垫/次要例子；重跑质检 |
| 正文段数 6+ | 拆得太碎 | 合并相邻段，保持 4～5 段 |
| docx 里还有参考资料 | 用了旧 builder/旧稿 | 用新 builder 重建；正文删“参考资料” |
| 文字和 docx 不一致 | 分身后来改了 txt | 等通知；按最新 txt 重建 docx |
| 质检 FAIL：来源 0 | 没写 `_sources.json` | 补来源文件；至少 2 条 |
| 质检 FAIL：声明缺失 | 用了旧长声明/漏写 | 统一短声明 |
| cron 没跑 | crontab 没装/PATH/代理/权限 | 看 `crontab -l`、`logs/cron/last_status.txt`、最新日志 |
| cron 跑了但失败 | 代理没起来/模型异常 | 看日志；手动 `DRY_RUN=1`/`bash daily_news_cron.sh` |
| 模型名警告 | deepseek 模型名不被 CLI 识别 | 不影响；确认输出正常 |
| 任务重叠 | 上一次没结束 | `flock` 会自动跳过；看日志 |
| 目录很乱 | 旧批次没归档 | 移入 `_v1_long/`/`_v2_first10/` |

---

# 13. 复现清单（Checklist）

从零复现今天的工作，按顺序打勾：

- [ ] 进入项目目录；
- [ ] 检查 Python 依赖（requests/bs4/lxml/docx/PIL）；
- [ ] 检查 claude CLI 可用；
- [ ] 检查 `crontab`/`flock`/`timeout`；
- [ ] 抓前 50 条：`collect_hot50.py --limit 50`；
- [ ] 过滤全部：`filter_topics.py`（不加 `--limit`）；
- [ ] 确认合格候选约 30～40 条；
- [ ] 读 `TOPIC_SELECTION_GUIDE.md`，做选题评审，选 10 + 5 备选；
- [ ] 用 `prepare_batch.py` 合并出 `_selected_full.json`；
- [ ] 按每批 5 条派写作分身，写 1200～1500 字、4～5 段；
- [ ] 每篇保存 `.txt` + `.sources.json` + `.images.json`；
- [ ] 下载图片，校验 3～5 张；
- [ ] 生成 docx；
- [ ] 跑文本质检 + Word 质检；
- [ ] 生成 `_index.md`；
- [ ] 归档旧批次；
- [ ] 检查 cron 干跑；
- [ ] 检查 `logs/cron/last_status.txt`；
- [ ] 确认最终 10 篇全部 PASS。

**预期结果**：

- 10 篇 txt；
- 10 篇 docx；
- 10 个 `_sources.json`；
- 10 个 `_images.json`；
- 10 个图片目录（每目录 3～5 张图 + `images_manifest.json`）；
- 1 个 `_index.md`；
- 全部 PASS。

---

# 14. 日常运维

## 14.1 每天看什么

```bash
cd /public/home/hpc/zhulei/superman/quant/code/news_search_writing
cat logs/cron/last_status.txt
ls -t logs/cron/news_*.log | head -1 | xargs tail -30
cat news_papers/$(date +%Y%m%d)/_index.md
```

看三件事：

1. 退出码是否 0；
2. 10 篇是否 PASS；
3. 有没有被备选替换的条目。

## 14.2 暂停定时任务

```bash
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
crontab -e
# 在行首加 # 注释掉：
# 0 5 * * * /public/home/.../daily_news_cron.sh
```

恢复：去掉 `#`，保存。

## 14.3 改条数/时间

- 改条数：编辑 `.claude/commands/news-write.md` 的默认条数，或改 cron 提示词里的“写10条”；
- 改时间：`crontab -e`，把 `0 5` 改成目标时间；
- 改字数：编辑 `NEWS_WRITING_GUIDE.md` 和两个 checker 的阈值。

## 14.4 手动跑一次

```bash
cd /public/home/hpc/zhulei/superman/quant/code/news_search_writing
bash daily_news_cron.sh
```

或只干跑：

```bash
DRY_RUN=1 bash daily_news_cron.sh
```

## 14.5 备份

```bash
# 备份今天成稿
cp -r news_papers/$(date +%Y%m%d) news_papers/$(date +%Y%m%d)_backup

# 备份 crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
```

---

# 15. 当前产物清单

## 15.1 最终 10 篇（2026-10-30，第三版）

| 写作顺序 | 榜单排名 | 成稿标题 | 字数 | 配图 | Word |
|---:|---:|---|---:|---:|---|
| 1 | 18 | 三本账看清养老金：崩盘论不成立，挑战须正视 | 1447 | 5 | `20261030_1113_01.docx` |
| 2 | 23 | 微信聊天记录要当证据，光靠截图不够 | 1497 | 3 | `20261030_1113_02.docx` |
| 3 | 11 | 10元快剪排起队，理发业该重算成本账 | 1495 | 5 | `20261030_1113_03.docx` |
| 4 | 17 | 模型第一、现金流转负：谷歌AI投入的账单 | 1473 | 5 | `20261030_1113_04.docx` |
| 5 | 19 | 老人入秋易怒多疑，未必只是脾气变差 | 1487 | 3 | `20261030_1113_05.docx` |
| 6 | 35 | 西班牙高铁事故首份报告：信号失灵后的致命放行 | 1499 | 4 | `20261030_1113_06.docx` |
| 7 | 24 | 11月起施行：社保、电动车、孩子用品都有新变化 | 1498 | 5 | `20261030_1113_07.docx` |
| 8 | 30 | 香飘飘单季净利不足百万：冲泡奶茶为何卖不动 | 1468 | 3 | `20261030_1113_08.docx` |
| 9 | 6 | 鸡蛋长斑先别扔，分清雀斑、暗斑与霉斑 | 1480 | 4 | `20261030_1113_09.docx` |
| 10 | 3 | ZXMOTO商标落定，创业者该补的知识产权课 | 1461 | 5 | `20261030_1113_10.docx` |

全部 PASS；图片合计 42 张；正文均 5 段；无参考资料；短声明齐全。

## 15.2 路径

```
news_papers/20261030/20261030_1113_01..10.txt/.sources.json/.images.json/.docx
news_papers/20261030/images_1115/01..10/
news_papers/20261030/_index.md
news_title/baidu_20261030_10-14_selected10.json
news_title/baidu_20261030_10-14_selected10_full.json
```

## 15.3 备份

```
news_papers/20261030/_v1_long/       # 第一版长文
news_papers/20261030/_v2_first10/    # 第二版压缩后的前10条
news_papers/20261030/_v2_first10/old_root/  # 第二版原文件
```

## 15.4 定时任务

```
0 5 * * * /public/home/hpc/zhulei/superman/quant/code/news_search_writing/daily_news_cron.sh
```

日志：

```
logs/cron/news_YYYYMMDD_HHMM.log
logs/cron/last_status.txt
```

---

# 16. 后续可改进

1. **压缩图片**：个别 docx 1.2MB（4096px 大图），可在下载时把最长边压到 1600px；
2. **发布环节**：可加“复制到头条”或头条 API（如果有）；
3. **通知**：成功/失败推送到微信（旧代码有 WxPusher，可复用）；
4. **来源校验**：发布前自动检查 `_sources.json` 的 URL 是否 200；
5. **图片内容校验**：OCR/人工抽查，避免图不对文；
6. **选题复盘**：把 selected/not_selected 理由做成日报，观察哪些选题阅读更好；
7. **git 提交**：每天/每周 checkpoint，代码+文档+成稿版本化；
8. **多平台适配**：同一篇内容生成公众号/小红书版本（需另写排版器）；
9. **数据看板**：统计每日字数、图片数、PASS/FAIL、替换条目；
10. **人工终审**：发布前人工看标题、首段、图片，避免敏感或事实错误。

---

# 17. 附录

## 17.1 过滤关键词（当前版本）

**涉政**：

```
全会、公报、中共中央、党中央、从严治党、党建、习近平、总书记、
政治局、纪委、监委、党史、红军、长征、国民党、第一书记、
外交部、国防部、台海、涉台、涉港、涉疆、涉藏、安倍、首相、
总统、大选、议会、政府工作报告
```

**股市实时行情**：

```
开盘、收盘、低开、高开、涨超、跌超、涨停、跌停、
沪指、深证成指、创业板指、科创50、KOSPI、韩股、
恒生指数、纳斯达克指数、道琼斯、标普500
```

**财经保留（分类用）**：

```
养老金、财报、净利、营收、银行、保险、基金、债券、利率、汇率、
货币政策、财政、税、贷款、存款、支付、消费金融、融资、市值、
股价、投资、理财、钱包
```

**手动剔除**：

```python
MANUAL_EXCLUDE = {
    "皇马因中国赞助": "涉外敏感：涉及中国赞助商与球员事件的表态",
}
```

> 关键词只是规则，边界条目仍需人工扫一眼；误删/漏删要调整规则或手动名单。

## 17.2 选题评分表

| 维度 | 权重 | 1～3 分 | 4～6 分 | 7～10 分 |
|---|---:|---|---|---|
| 公共价值 | 30% | 小众/猎奇 | 一般社会话题 | 影响多数人的钱/健康/安全/权益 |
| 可写性 | 20% | 只有一句摘要 | 有 1～2 篇报道 | 2～3 个可靠来源、事实充足 |
| 配图 | 15% | 无图/只有 logo | 1～2 张可用 | 3 张以上相关图 |
| 多样性 | 20% | 与已选同质 | 同领域但角度不同 | 补足新领域、去重 |
| 风险 | 15% | 高敏感/未证实 | 需克制 | 低风险、官方来源 |
| 热度 | 加分 | 排名低 | 中 | 排名高 |

## 17.3 写作 Prompt 模板

```text
你是新闻解读流水线的“写作分身”，负责本次第 X 条（榜单第 Y 名）。

【必读】先完整阅读：
/public/home/hpc/zhulei/superman/quant/code/news_search_writing/NEWS_WRITING_GUIDE.md

【本条热点】
榜单排名：Y
本次序号：X
原标题：...
摘要：...
百度搜索链接：...

【任务】
1. 用 WebSearch 做 2～3 次中文搜索，核实事实、背景、各方反应。
2. 不要使用 WebFetch；用
   python .../20261030_fetch_page_text.py "网址1" "网址2"
   读 1～3 篇原文。
3. 按规范写纯文本：标题≤30字；正文4～5段、1200～1500字；
   正文不出现“参考资料”；文末只写短声明。
   保存到：.../news_papers/<日期>/<stamp>_<序号>.txt
4. 来源保存到同名 .sources.json（2～5 条）。
5. 用 extract_images.py 挑 5 个图片候选，保存到同名 .images.json。
6. 不要自己下载图片，不要生成 docx。
7. 保存后只返回一行 JSON：
   {"rank": Y, "batch_index": X, "file": "...", "sources_file": "...",
    "images_file": "...", "headline": "...", "body_chars": 1350,
    "paragraphs": 5, "sources": ["..."], "images_count": 5,
    "status": "ok", "note": ""}
```

## 17.4 压缩/精简 Prompt 模板

```text
你是“精简编辑”，负责把一篇已完成的新闻解读压缩到 1200～1500 字。

【必读】NEWS_WRITING_GUIDE.md
【现有文章】...
【任务】
1. 压缩成 1200～1500 字、4～5 段。
2. 保留关键事实/数字/观点/分寸；删除重复铺垫、次要例子、参考资料。
3. 不新增原文没有的事实；不改变立场；不写成要点列表。
4. 文末只保留短声明：
   声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。
5. 正文不能出现“参考资料”。
6. 覆盖保存原路径；不要改 .sources.json/.images.json/.docx。
7. 返回 JSON：{"batch_index": X, "body_chars": ..., "paragraphs": ..., "headline": "..."}
```

## 17.5 Cron Prompt（脚本里的实际内容）

```text
读取并严格执行 .../.claude/commands/news-write.md 的完整流程：
抓取百度热榜、过滤涉政和股市实时行情，
然后从过滤后的全部候选里按 TOPIC_SELECTION_GUIDE.md 评审并选出10条+备选
（不要直接取前10条），再写作、配图、生成docx、质检、生成索引。
正文1200～1500字，4～5段；正文不出现参考资料，来源另存 _sources.json；
文末只保留一句图片版权声明。不要询问，直接执行完。
```

## 17.6 常用路径

```
项目根：/public/home/hpc/zhulei/superman/quant/code/news_search_writing
抓取：20261030_collect_hot50.py
过滤：20261030_filter_topics.py
选题：TOPIC_SELECTION_GUIDE.md
合并：20261030_prepare_batch.py
写作：NEWS_WRITING_GUIDE.md
读网页：20261030_fetch_page_text.py
图片：20261030_extract_images.py / 20261030_download_images.py
docx：20261030_build_docx.py
质检：20261030_check_articles.py / 20261030_check_docx.py
定时：daily_news_cron.sh
一键：.claude/commands/news-write.md
```

---

# 结语

这份指南的核心不是“某一次的具体文章”，而是**一套可重复的加工流水线**：

1. **选得对**：从全部合格候选里选，不取前 10；
2. **写得短**：1200～1500 字，适合头条完读率；
3. **有图有源**：3～5 张图，来源可追溯；
4. **发布版干净**：正文无参考资料，只留短声明；
5. **可质检**：文本 + Word 双质检，PASS 才交付；
6. **能自动**：每天 5:00 跑，日志可查，失败可排查；
7. **可复现**：所有脚本、格式、命令、教训都在这份文档里。

后续如果调整字数、条数、时间、选题标准，按第 14 节改对应文件，再跑一遍第 13 节 Checklist 即可。
