#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成稿质检器（Claude Code 专用版）

作用：
    对一批新闻解读成稿做自动检查，检查项包括：
        1. 文件是否存在、是否为空；
        2. 标题是否 ≤ 30 字；
        3. 正文是否 4～5 段、是否约 2000 字；
        4. 是否有“参考资料”且至少 2 条来源；
        5. 是否有固定免责声明；
        6. 是否有 Markdown 标记、占位符等不合格内容。

用法：
    python 20261030_check_articles.py \
        --dir news_papers/20261030 \
        --prefix 20261030_1015 \
        --count 10 \
        --worklist news_title/baidu_20261030_09-30_10.json \
        --index news_papers/20261030/_index.md

输出：
    - 终端打印一张检查表；
    - 如果指定 --index，会生成一个 Markdown 索引文件；
    - 全部通过时退出码为 0，有不合格项时退出码为 1。
"""

import argparse
import json
import os
import re
import sys

# ====================== 判定标准 ======================
TITLE_MAX = 30                 # 标题最多 30 字
BODY_MIN_PASS = 1200           # 正文 1200～1500 字为“合格”
BODY_MAX_PASS = 1500
BODY_MIN_WARN = 1100           # 1100～1200 / 1500～1600 字为“警告”
BODY_MAX_WARN = 1600
PARA_PASS = {4, 5}             # 4～5 段为合格
PARA_WARN = {3, 6}             # 3 段或 6 段为警告
MIN_SOURCES = 2                # 来源清单至少 2 条（存在 _sources.json 里）

DISCLAIMER = "声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。"

PLACEHOLDERS = [
    "此处省略", "待补充", "TODO", "XXX", "xxx",
    "……（正文过长", "[待补充]", "【待补充】",
]


def count_chars(text):
    """统计正文有效字数：去掉所有空白字符后的长度。"""
    return len(re.sub(r"\s", "", text))


def split_article(raw):
    """
    把成稿拆成：标题、正文段落、旧参考资料（如果有）、声明。

    新格式的文章没有“参考资料”，只有：
        第 1 行：标题
        正文若干行
        声明：本文图片来源于网络，版权归原作者所有，如有侵权请联系删除。

    为了兼容旧稿，如果文章里还有“参考资料：”，也仍然能正确拆开。
    """
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return "", [], [], ""

    title = lines[0]

    # 找“参考资料”和“声明”的位置
    ref_index = None
    disclaimer_index = None
    for i, line in enumerate(lines):
        if ref_index is None and re.match(r"^参考资料\s*[：:]", line):
            ref_index = i
        if disclaimer_index is None and line.startswith("声明："):
            disclaimer_index = i

    # 正文到“参考资料”或“声明”中较早的那个为止
    ends = [x for x in (ref_index, disclaimer_index, len(lines)) if x is not None]
    body_end = min(ends)
    body_lines = lines[1:body_end]

    # 旧稿的参考资料（新稿一般为空）
    if ref_index is not None:
        ref_end = disclaimer_index if disclaimer_index is not None and disclaimer_index > ref_index else len(lines)
        ref_lines = lines[ref_index + 1:ref_end]
    else:
        ref_lines = []

    disclaimer = lines[disclaimer_index] if disclaimer_index is not None else ""
    return title, body_lines, ref_lines, disclaimer


def check_one(rank, path):
    """检查一篇文章，返回一个结果字典。"""
    result = {
        "rank": rank,
        "file": path,
        "exists": os.path.exists(path),
        "status": "FAIL",
        "issues": [],
        "warnings": [],
        "title": "",
        "title_len": 0,
        "paragraphs": 0,
        "body_chars": 0,
        "sources": 0,
    }

    if not os.path.exists(path):
        result["issues"].append("文件不存在")
        return result

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    if not raw.strip():
        result["issues"].append("文件为空")
        return result

    title, body_lines, ref_lines, disclaimer = split_article(raw)
    result["title"] = title
    result["title_len"] = len(title)
    result["paragraphs"] = len(body_lines)
    result["body_chars"] = count_chars("\n".join(body_lines))

    # ---------- 1. 标题 ----------
    if not title:
        result["issues"].append("没有标题")
    elif result["title_len"] > TITLE_MAX:
        result["issues"].append(
            f"标题 {result['title_len']} 字，超过 {TITLE_MAX} 字"
        )

    # ---------- 2. 段落数 ----------
    if result["paragraphs"] not in PARA_PASS:
        if result["paragraphs"] in PARA_WARN:
            result["warnings"].append(
                f"正文 {result['paragraphs']} 段，建议 4～5 段"
            )
        else:
            result["issues"].append(
                f"正文 {result['paragraphs']} 段，不符合 4～5 段"
            )

    # ---------- 3. 正文字数 ----------
    chars = result["body_chars"]
    if chars < BODY_MIN_PASS or chars > BODY_MAX_PASS:
        if BODY_MIN_WARN <= chars <= BODY_MAX_WARN:
            result["warnings"].append(
                f"正文 {chars} 字，建议 1200～1500 字"
            )
        else:
            result["issues"].append(
                f"正文 {chars} 字，超出 1100～1600 字范围"
            )

    # ---------- 4. 来源清单（不放进正文，另存 _sources.json） ----------
    sources_path = path.replace(".txt", ".sources.json")
    if os.path.exists(sources_path):
        try:
            with open(sources_path, "r", encoding="utf-8") as f:
                source_payload = json.load(f)
            result["sources"] = len(source_payload.get("sources", []))
        except Exception:
            result["sources"] = 0
    else:
        # 兼容旧稿：如果正文里还有参考资料，就按正文里的条数算
        source_lines = [
            line for line in ref_lines if re.match(r"^\d+\s*[.、]", line)
        ]
        urls = re.findall(r"https?://\S+", "\n".join(ref_lines))
        result["sources"] = max(len(source_lines), len(urls))

    if result["sources"] == 0:
        result["warnings"].append("没有找到来源清单（_sources.json）")
    elif result["sources"] < MIN_SOURCES:
        result["warnings"].append(
            f"来源清单只有 {result['sources']} 条，建议至少 {MIN_SOURCES} 条"
        )

    # ---------- 5. 免责声明（短句） ----------
    if DISCLAIMER not in raw:
        result["issues"].append("图片版权声明缺失或被改动")

    # ---------- 6. 占位符 ----------
    for marker in PLACEHOLDERS:
        if marker in raw:
            result["issues"].append(f"出现占位符：{marker}")

    # ---------- 7. Markdown 标记 ----------
    if "**" in raw or re.search(r"^#{1,6}\s", raw, re.MULTILINE):
        result["issues"].append("出现 Markdown 标记（** 或 #）")
    if "```" in raw:
        result["issues"].append("出现代码块标记")

    # ---------- 8. 结论 ----------
    if result["issues"]:
        result["status"] = "FAIL"
    elif result["warnings"]:
        result["status"] = "WARN"
    else:
        result["status"] = "PASS"

    return result


def load_worklist(path):
    """
    读取工作清单，返回 {本次序号: item}。

    兼容两种格式：
        - 采集脚本原始 JSON：items 列表，用 rank 作序号；
        - 过滤脚本 JSON：kept 列表，用 batch_index 作本次序号。
    """
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    items = payload.get("items") or payload.get("kept") or []
    result = {}
    for item in items:
        key = item.get("batch_index", item.get("rank"))
        result[key] = item
    return result


def escape_md(text):
    """转义 Markdown 表格里的竖线。"""
    return (text or "").replace("|", "\\|")


def write_index(path, results, worklist, title_prefix):
    """
    生成 Markdown 索引：
        本次序号 ↔ 榜单排名 ↔ 原标题 ↔ 成稿标题 ↔ txt/docx ↔ 字数/段数/来源/状态。
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lines = [
        f"# {title_prefix} 百度热榜新闻解读索引",
        "",
        "| 本次序号 | 榜单排名 | 原标题 | 成稿标题 | 文件 | 正文字数 | 段数 | 来源数 | 状态 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        rank = result["rank"]
        item = worklist.get(rank, {})
        original = item.get("title", "（未知）")
        original_rank = item.get("rank", "—")
        file_name = os.path.basename(result["file"])
        docx_name = file_name.replace(".txt", ".docx")
        docx_path = os.path.join(os.path.dirname(result["file"]), docx_name)
        docx_mark = docx_name if os.path.exists(docx_path) else "—"
        lines.append(
            "| {rank} | {original_rank} | {original} | {headline} | txt：{file}；docx：{docx} | {chars} | {paras} | {sources} | {status} |".format(
                rank=rank,
                original_rank=original_rank,
                original=escape_md(original),
                headline=escape_md(result["title"]),
                file=file_name,
                docx=docx_mark,
                chars=result["body_chars"],
                paras=result["paragraphs"],
                sources=result["sources"],
                status=result["status"],
            )
        )
    lines.append("")
    lines.append("> 状态说明：PASS = 全部合格；WARN = 有提醒项但可用；FAIL = 需要返工。")
    lines.append("> docx 列：显示 Word 文件名表示已生成；“—”表示还没生成。")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n索引已生成：{path}")


def main():
    parser = argparse.ArgumentParser(description="批量检查新闻解读成稿")
    parser.add_argument(
        "--dir", required=True, help="成稿所在目录，例如 news_papers/20261030"
    )
    parser.add_argument(
        "--prefix", required=True, help="文件名前缀，例如 20261030_1015"
    )
    parser.add_argument(
        "--count", type=int, required=True, help="本次预期篇数"
    )
    parser.add_argument(
        "--worklist", default=None, help="采集脚本生成的 JSON 工作清单"
    )
    parser.add_argument(
        "--index", default=None, help="生成 Markdown 索引的路径（可选）"
    )
    args = parser.parse_args()

    worklist = load_worklist(args.worklist)
    results = []

    print(f"检查目录：{args.dir}")
    print(f"文件前缀：{args.prefix}")
    print(f"预期篇数：{args.count}")
    print("=" * 96)
    print(
        f"{'序号':<4}{'状态':<8}{'标题字数':<8}{'段数':<6}{'正文字数':<10}{'来源数':<6}问题"
    )
    print("-" * 96)

    for rank in range(1, args.count + 1):
        path = os.path.join(args.dir, f"{args.prefix}_{rank:02d}.txt")
        result = check_one(rank, path)
        results.append(result)

        problems = result["issues"] + result["warnings"]
        problem_text = "；".join(problems) if problems else "—"
        print(
            f"{rank:<4}{result['status']:<8}{result['title_len']:<8}"
            f"{result['paragraphs']:<6}{result['body_chars']:<10}"
            f"{result['sources']:<6}{problem_text}"
        )

    print("=" * 96)
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"结果：PASS {passed} 篇，WARN {warned} 篇，FAIL {failed} 篇，共 {len(results)} 篇")

    if failed:
        print("\n需要返工的文章：")
        for result in results:
            if result["status"] == "FAIL":
                print(f"  - 第 {result['rank']} 篇：{'；'.join(result['issues'])}")

    if args.index:
        write_index(
            args.index,
            results,
            worklist,
            os.path.basename(os.path.abspath(args.dir)),
        )

    # 有 FAIL 时返回非 0，方便主流程判断
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
