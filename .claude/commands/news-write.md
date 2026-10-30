---
description: 抓取百度热榜，过滤涉政/股市行情，从全部合格候选里选 10 条写成带图 docx
argument-hint: [要写的条数，默认 10]
---

执行“百度热榜新闻解读”流水线。本次要写的条数：$ARGUMENTS（如果为空，按 10 条执行）。

工作目录：`/public/home/hpc/zhulei/superman/quant/code/news_search_writing`

完整流程、规则和故障排查见 `NEWS_WORKFLOW_OPERATIONS_GUIDE.md`。

**重要：不是过滤后取前 N 条，而是从全部合格候选里按标准挑 N 条。**

严格按以下步骤执行：

1. **采集**
   ```bash
   python 20261030_collect_hot50.py --limit 50
   ```
   记下输出里的 `run_stamp` 和 JSON 工作清单路径。

2. **过滤（不要截断）**
   ```bash
   python 20261030_filter_topics.py \
     --worklist <上一步的 JSON> \
     --out <过滤后的 JSON>
   ```
   - 规则：剔除涉政类、股市实时行情类；保留财政、金融、公司财报、消费金融等财经新闻。
   - **不要加 `--limit`**，保留全部合格候选（通常 30～40 条）。
   - 把过滤后的 `kept` 清单读一遍，确认没有误留/误删。

3. **选题评审（关键步骤）**
   - 先完整阅读 `TOPIC_SELECTION_GUIDE.md`。
   - 读取过滤后的**全部** `kept` 候选。
   - 按公共价值、可写性、配图可得性、领域多样性、风险控制打分；热度只作加分项。
   - 选 **N 条（默认 10）+ 3～5 条备选**；同一事件/人物只选 1 条；至少覆盖 4 个领域。
   - 保存 `news_title/<run_stamp>_selected.json`，格式见 `TOPIC_SELECTION_GUIDE.md`。
   - 选中的条目按 `batch_index` 1～N 重新编号，后续写作按这个顺序。
   - **不要直接取前 N 条**；每条选择都要写清 `reason`。
   - 运行合并脚本，把选题结果和原始榜单合成写作清单：
     ```bash
     python 20261030_prepare_batch.py \
       --worklist news_title/<run_stamp>_50.json \
       --selection news_title/<run_stamp>_selected.json \
       --out news_title/<run_stamp>_selected_full.json
     ```
   - 后续写作和质检都使用 `_selected_full.json`。

4. **写作 + 选图**
   - 先完整阅读 `NEWS_WRITING_GUIDE.md`。
   - 按每批 5 条派发“写作分身”（Agent 工具，general-purpose）。
   - 每个分身必须：
     - 用 WebSearch 检索，不要用 WebFetch；
     - 用 `20261030_fetch_page_text.py` 读原文；
     - 写 4～5 段、1200～1500 字的纯文本，保存为
       `news_papers/<日期>/<run_stamp>_<本次序号两位数>.txt`；
     - **正文不要写“参考资料”**；把来源保存到同名的 `.sources.json`；
     - 文末只写一句：“声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。”
     - 用 `20261030_extract_images.py` 从来源页挑 5 个候选图，
       保存为同名的 `.images.json`；
     - 不要自己下载图片，不要生成 docx。
   - 如果某条检索后发现资料不足、配图不足，或事实无法核实：
     - 不要硬写；
     - 从 `backups` 里按顺序递补；
     - 在最终汇报里说明哪条被替换、为什么。
   - 每批等全部完成，再派下一批，避免搜索限流。

5. **下载图片并校验**
   对每一篇：
   ```bash
   python 20261030_download_images.py \
     --manifest news_papers/<日期>/<run_stamp>_<序号>.images.json \
     --outdir news_papers/<日期>/images/<序号> \
     --min-count 3 --max-count 5
   ```
   少于 3 张合格图的，补候选或换来源后重跑；仍不够，考虑用备选替换。

6. **生成 docx**
   ```bash
   python 20261030_build_docx.py \
     --txt news_papers/<日期>/<run_stamp>_<序号>.txt \
     --images news_papers/<日期>/images/<序号>/images_manifest.json \
     --out news_papers/<日期>/<run_stamp>_<序号>.docx \
     --rank <榜单排名> --original-title "<原标题>"
   ```

7. **质检 + 索引**
   ```bash
   python 20261030_check_articles.py \
     --dir news_papers/<日期> --prefix <run_stamp> --count <条数> \
     --worklist <selected.json> \
     --index news_papers/<日期>/_index.md

   python 20261030_check_docx.py \
     --dir news_papers/<日期> --prefix <run_stamp> --count <条数>
   ```
   - 对 FAIL 的篇目返工；全部 PASS/WARN 后再结束。
   - docx 生成后重跑一次 `check_articles.py --index`，让索引里的 docx 列变成“有”。

8. **汇报**
   报告：成功篇数、被过滤掉的条目、**选题理由摘要**、每篇图片张数、docx 路径、索引路径。
   不要粘贴全文。

注意：
- 全程不调用火山引擎、硅基流动或任何外部 AI API。
- 不推送微信（除非用户明确要求）。
- 不修改旧脚本。
- 涉政类、股市实时行情类一律不写；财政/金融类保留。
- 10 条是从全部合格候选里选出来的，不是前 10 条。
