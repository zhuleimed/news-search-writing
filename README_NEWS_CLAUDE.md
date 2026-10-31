# 百度热榜新闻解读（Claude Code 版 v2）

这套工具把原来的“火山引擎智能体写作”换成了 **Claude Code 自己检索、自己写**，
并新增了五件事：

1. **选题过滤**：自动剔除涉政类、股市实时行情类；保留财政、金融、公司财报等财经新闻；
2. **选题评审**：从过滤后的全部候选里按标准挑 10 条 + 备选，**不是直接取前 10 条**；
3. **配图**：每篇从新闻原文中挑 3～5 张相关图片，下载校验后插入文章；
4. **Word 排版**：生成符合头条图文阅读习惯的 `.docx`；
5. **头条长度**：正文 1200～1500 字、4～5 段；正文不出现参考资料，来源另存 `_sources.json`；
   文末只保留一句图片版权声明。

全程不需要任何 AI API Key。

> **完整复现指南**：见 `NEWS_WORKFLOW_OPERATIONS_GUIDE.md`（需求演变、完整流程、规则、数据格式、今天的经过、教训、故障排查、复现清单）。

## 每天 5:00 定时任务

系统 crontab 已配置：

```
0 5 * * * /public/home/hpc/zhulei/superman/quant/code/news_search_writing/daily_news_cron.sh
```

- 脚本：`daily_news_cron.sh`；
- 日志：`logs/cron/news_YYYYMMDD_HHMM.log`；
- 状态：`logs/cron/last_status.txt`；
- 防止重叠：`flock`；
- 最长运行：3 小时（`timeout 10800`）；
- 干跑测试：`DRY_RUN=1 bash daily_news_cron.sh`；
- 预检：`claude` 是否存在、`deepseek_proxy.py` 是否在运行、认证变量是否已加载；
- 认证：cron 不继承登录 shell 的 `ANTHROPIC_AUTH_TOKEN`；脚本会 source
  `/home/zhulei/.config/news_search_writing/claude_env.sh`（仓库外，600 权限）。
  如果日志出现 `Not logged in`，按 `NEWS_WORKFLOW_OPERATIONS_GUIDE.md` 4.7 重新生成。

## 一条命令复用

在 Claude Code 里输入：

```
/news-write 10
```

数字是要写的条数（不填默认 10）。它会自动完成：
抓取 → 过滤 → 选题评审 → 检索写作 → 选图 → 下载校验 → 生成 docx → 质检 → 索引。

## 主要文件各管什么

| 文件 | 作用 |
|---|---|
| `20261030_collect_hot50.py` | 抓百度热榜前 N 条，存 TXT + JSON |
| `20261030_filter_topics.py` | 剔除涉政/股市行情，保留财经类 |
| `TOPIC_SELECTION_GUIDE.md` | 选题评审标准（公共价值、可写性、配图、多样性、风险） |
| `20261030_prepare_batch.py` | 把选题结果和原始榜单合并成写作批次清单 |
| `20261030_fetch_page_text.py` | 打开新闻网页、提取正文 |
| `20261030_extract_images.py` | 列出新闻网页里的候选图片地址 |
| `20261030_download_images.py` | 下载图片、校验尺寸/比例/重复 |
| `20261030_build_docx.py` | 生成头条风格 Word（1200～1500 字、无参考资料、短声明） |
| `20261030_check_articles.py` | 检查纯文本成稿 + 生成索引 |
| `20261030_check_docx.py` | 检查 Word 的图片数/标题/声明 |
| `daily_news_cron.sh` | 每天 5:00 的定时任务入口 |
| `NEWS_WRITING_GUIDE.md` | 写作规范（角色、结构、字数、来源、配图、敏感题材） |
| `NEWS_WORKFLOW_OPERATIONS_GUIDE.md` | 完整复现指南（流程、规则、数据格式、教训、故障排查） |

## 手动执行（不用斜杠命令时）

```bash
# 1. 抓前 50 条
python 20261030_collect_hot50.py --limit 50

# 2. 过滤（不要加 --limit，保留全部合格候选）
python 20261030_filter_topics.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --out news_title/baidu_20261030_10-14_50_filtered_all.json

# 3. 选题评审：让 Claude Code 按 TOPIC_SELECTION_GUIDE.md
#    从全部 kept 候选里选 10 条 + 5 条备选
#    结果：news_title/baidu_20261030_10-14_selected10.json

# 3.5 合并成写作批次（带摘要和百度链接）
python 20261030_prepare_batch.py \
  --worklist news_title/baidu_20261030_10-14_50.json \
  --selection news_title/baidu_20261030_10-14_selected10.json \
  --out news_title/baidu_20261030_10-14_selected10_full.json

# 4. 让 Claude Code 按 NEWS_WRITING_GUIDE.md 逐条检索、写作、选图
#    正文 1200～1500 字、4～5 段；正文不写参考资料
#    成稿：news_papers/20261030/20261030_1014_01.txt ...
#    来源：同名的 .sources.json
#    图片候选：同名的 .images.json

# 5. 下载图片（每篇）
python 20261030_download_images.py \
  --manifest news_papers/20261030/20261030_1014_01.images.json \
  --outdir news_papers/20261030/images/01 \
  --min-count 3 --max-count 5

# 6. 生成 Word（每篇）
python 20261030_build_docx.py \
  --txt news_papers/20261030/20261030_1014_01.txt \
  --images news_papers/20261030/images/01/images_manifest.json \
  --out news_papers/20261030/20261030_1014_01.docx \
  --rank 3 --original-title "“张雪机车”商标终于归“张雪”了"

# 7. 质检 + 索引
python 20261030_check_articles.py \
  --dir news_papers/20261030 --prefix 20261030_1014 --count 10 \
  --worklist news_title/baidu_20261030_10-14_10_filtered.json \
  --index news_papers/20261030/_index.md

python 20261030_check_docx.py \
  --dir news_papers/20261030 --prefix 20261030_1014 --count 10
```

## 选题过滤规则

**剔除：**

- 涉政：党的会议、公报、领导人、从严治党、党建、党史、外交/国防等；
- 股市实时行情：开盘/收盘/低开/高开/涨超/跌超/涨停/跌停/指数点位等。

**保留：**

- 财政、金融：养老金、银行、保险、基金、债券、利率、汇率、财政、税、贷款、存款、支付、消费金融等；
- 公司财报、消费金融、财经商业分析等。

> 过滤脚本用的是关键词规则，个别边界条目会在终端列出“剔除原因”，
> 运行后需要人工扫一眼，避免误删或漏删。

## 选题评审（不是取前 10 条）

- 过滤后通常还剩 30～40 条；**不是按排名取前 10 条**。
- 由“选题主编”按 `TOPIC_SELECTION_GUIDE.md` 评分：
  公共价值 30%、可写性 20%、配图可得性 15%、领域多样性 20%、风险控制 15%；
  热度只作加分项。
- 选 **10 条 + 3～5 条备选**；同一事件/人物只选 1 条；至少覆盖 4 个领域。
- 结果保存 `news_title/<run_stamp>_selected.json`，每条都有选择理由。
- 写作时如果某条资料/配图不足，从备选里递补。

## 图片规则

- 只从文章实际引用过的新闻页面取图；
- 每篇 3～5 张，下载时自动校验：宽 ≥ 400px、高 ≥ 250px、比例 0.4～2.6、内容不重复；
- 每张图都有说明和来源（例：“商标公告截图（来源：国家知识产权局商标局）”）；
- 不要 logo、二维码、头像、广告位；
- 事故、犯罪类题材避免血腥、遗体和可识别的受害者照片。

## Word 排版

- 标题：22 磅加粗，左对齐；
- 标题下：一行灰色小字“全文约 XXXX 字 · 配图 X 张”；
- 正文：12 磅微软雅黑，1.5 倍行距，长段落在 Word 里拆成短段，手机上更好读；
- 配图：居中，横图最大 15.5 厘米宽、竖图最高 18 厘米，图下 9 磅灰色说明；
- 文末：只保留一句图片版权声明，9 磅灰色；**不再放参考资料**。

## 输出目录

```
news_title/
  baidu_20261030_10-14_50.txt              # 原始榜单
  baidu_20261030_10-14_50.json             # 工作清单
  baidu_20261030_10-14_50_filtered_all.json # 过滤后的全部候选（约30～40条）
  baidu_20261030_10-14_selected10.json     # 选题评审选出的10条+备选

news_papers/20261030/
  20261030_1014_01.txt                     # 纯文本（1200～1500 字，无参考资料）
  20261030_1014_01.sources.json            # 来源清单（内部核对，不进正文）
  20261030_1014_01.images.json             # 图片候选
  20261030_1014_01.docx                    # Word 成稿
  images/01/img_01.jpg ...                 # 下载后的图片
  images/01/images_manifest.json           # 最终图片清单
  _index.md                                # 总索引
```

## 和旧流程的区别

| 项目 | 旧流程 | 新流程 |
|---|---|---|
| 写作引擎 | 火山引擎 bot / 硅基流动 API | Claude Code 自己 |
| 是否需要 Key | 需要 `ARK_API_KEY` 等 | 不需要 |
| 选题过滤 | 无 | 剔除涉政/股市行情，保留财经 |
| 配图 | 无 | 每篇 3～5 张，带来源说明 |
| 字数 | 约 2000 字 | 1200～1500 字，更适合头条完读率 |
| 参考资料 | 放在正文末尾 | 不进正文，另存 `_sources.json` |
| 输出格式 | .txt | .txt + .docx（头条排版） |
| 质检 | 无 | 文本 + Word 双质检 |
| 定时任务 | 无 | 每天 5:00 自动跑 10 条 |
| 可追溯性 | 文件名只有序号 | 索引记录本次序号、榜单排名、原标题、成稿、图片数、来源数 |

## 注意

1. `WebFetch` 在本机被安全策略拦截，所以统一用 `20261030_fetch_page_text.py` 读网页。
2. 知乎、部分公众号、需要登录的页面可能抓不到，换其他来源即可。
3. 图片版权：文章末尾有一句图片版权声明，每张图也标注来源；如需商用，请自行确认授权。
4. 旧脚本（火山引擎版）保持原样，没有改动。
