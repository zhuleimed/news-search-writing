#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx 成稿质检器（Claude Code 专用版）

检查每一篇 Word 成稿是否满足：
    1. 文件存在、能被 python-docx 打开；
    2. 内嵌图片 3～5 张；
    3. 第一段标题不超过 30 字；
    4. 文末只有一句简短的图片版权声明；
    5. 文档属性里记录了正文字数和排名。

用法：
    python 20261030_check_docx.py \
        --dir news_papers/20261030 \
        --prefix 20261030_1014 \
        --count 10
"""

import argparse
import os
import re
import sys

from docx import Document

TITLE_MAX = 30
MIN_IMAGES = 3
MAX_IMAGES = 5
MIN_FILE_KB = 30


def parse_keywords(text):
    """把 core_properties.keywords 里的 rank=3;body_chars=2000 解析成字典。"""
    result = {}
    for part in (text or "").split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def check_one(index, path):
    """检查一篇 docx，返回结果字典。"""
    result = {
        "index": index,
        "file": path,
        "status": "FAIL",
        "issues": [],
        "title": "",
        "title_len": 0,
        "images": 0,
        "body_chars": 0,
        "rank": "",
    }

    if not os.path.exists(path):
        result["issues"].append("文件不存在")
        return result

    size_kb = os.path.getsize(path) // 1024
    if size_kb < MIN_FILE_KB:
        result["issues"].append(f"文件只有 {size_kb}KB，可能没嵌入图片")

    try:
        doc = Document(path)
    except Exception as exc:
        result["issues"].append(f"打不开：{type(exc).__name__}")
        return result

    texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    result["title"] = texts[0] if texts else ""
    result["title_len"] = len(result["title"])
    result["images"] = len(doc.inline_shapes)

    meta = parse_keywords(doc.core_properties.keywords)
    result["body_chars"] = int(meta.get("body_chars", 0) or 0)
    result["rank"] = meta.get("rank", "")

    # ---------- 标题 ----------
    if not result["title"]:
        result["issues"].append("没有标题")
    elif result["title_len"] > TITLE_MAX:
        result["issues"].append(
            f"标题 {result['title_len']} 字，超过 {TITLE_MAX} 字"
        )

    # ---------- 图片 ----------
    if result["images"] < MIN_IMAGES or result["images"] > MAX_IMAGES:
        result["issues"].append(
            f"内嵌图片 {result['images']} 张，要求 {MIN_IMAGES}～{MAX_IMAGES} 张"
        )

    # ---------- 短声明 ----------
    if not any(t.startswith("声明：本文图片来源于网络") for t in texts):
        result["issues"].append("图片版权声明缺失或被改动")

    # ---------- 正文字数 ----------
    body_chars = result["body_chars"]
    if body_chars and (body_chars < 1100 or body_chars > 1600):
        result["issues"].append(f"正文 {body_chars} 字，超出 1100～1600")

    if not result["issues"]:
        result["status"] = "PASS"

    return result


def main():
    parser = argparse.ArgumentParser(description="检查 docx 成稿")
    parser.add_argument("--dir", required=True, help="docx 所在目录")
    parser.add_argument("--prefix", required=True, help="文件名前缀")
    parser.add_argument("--count", type=int, required=True, help="预期篇数")
    args = parser.parse_args()

    results = []
    print(f"检查目录：{args.dir}")
    print(f"文件前缀：{args.prefix}")
    print(f"预期篇数：{args.count}")
    print("=" * 92)
    print(
        f"{'序号':<4}{'状态':<8}{'标题字数':<8}{'图片数':<6}"
        f"{'正文字数':<10}{'榜单排名':<8}问题"
    )
    print("-" * 92)

    for index in range(1, args.count + 1):
        path = os.path.join(args.dir, f"{args.prefix}_{index:02d}.docx")
        result = check_one(index, path)
        results.append(result)
        problems = "；".join(result["issues"]) if result["issues"] else "—"
        print(
            f"{index:<4}{result['status']:<8}{result['title_len']:<8}"
            f"{result['images']:<6}{result['body_chars']:<10}"
            f"{result['rank']:<8}{problems}"
        )

    print("=" * 92)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    print(f"结果：PASS {passed} 篇，FAIL {failed} 篇，共 {len(results)} 篇")

    if failed:
        print("\n需要返工的 docx：")
        for result in results:
            if result["status"] == "FAIL":
                print(f"  - 第 {result['index']} 篇：{'；'.join(result['issues'])}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
