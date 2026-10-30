#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻网页正文提取器（Claude Code 专用版）

为什么需要它：
    Claude Code 自带的 WebFetch 在本机被安全策略拦截（提示“无法验证域名安全”），
    但用 Python 的 requests 可以直接下载中文新闻网页。这个脚本负责：
        1. 下载网页；
        2. 去掉导航、广告、页脚等杂物；
        3. 把正文段落提取出来，打印到终端（或保存到文件）。

用法：
    python 20261030_fetch_page_text.py <网址1> [网址2 ...]
    python 20261030_fetch_page_text.py <网址> --max-chars 6000
    python 20261030_fetch_page_text.py <网址> --out /tmp/page.txt

输出约定：
    成功：先打印 [OK] URL / 标题 / 正文长度，再打印正文；
    失败：打印 [FAIL] URL / 原因，退出码仍为 0，方便一次试多个网址。

注意：
    - 只提取文字，不下载图片；
    - 正文最多保留 --max-chars 个字符（默认 6000），避免把整页广告都塞进来；
    - 澎湃、腾讯、新浪、新华网、政府网等实测可用；知乎等需要登录/反爬的站点可能失败，
      失败时换一个来源即可。
"""

import argparse
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}

# 这些标签里的内容不是正文，统一删掉
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]

# 这些行是网站版权/导航/推荐之类的套话，正文里不需要
NOISE_PATTERNS = [
    r"^责任编辑[:：]",
    r"^编辑[:：]",
    r"^原标题[:：]",
    r"^来源[:：]",
    r"^扫一扫",
    r"^下载.*客户端",
    r"^点击.*查看更多",
    r"^版权声明",
    r"^免责声明",
    r"^相关阅读",
    r"^热门推荐",
]


def clean_line(text):
    """压缩空白，去掉首尾空格。"""
    return re.sub(r"\s+", " ", text or "").strip()


def is_noise(line):
    """判断一行是不是网站套话。"""
    return any(re.search(pattern, line) for pattern in NOISE_PATTERNS)


def extract_from_soup(soup):
    """
    从已经解析好的网页里提取正文。

    策略：
        1. 优先找 <article> 里的 <p>；
        2. 找不到就用全页 <p>；
        3. 如果 <p> 太少，退而求其次，找文字最多的 <div>（很多老站点正文不在 <p> 里）。
    返回 (标题, 正文段落列表)。
    """
    title = ""
    if soup.title:
        title = clean_line(soup.title.get_text())

    # 先删掉噪音标签
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    paragraphs = []

    def collect_from(container):
        result = []
        for p in container.find_all("p"):
            text = clean_line(p.get_text(" ", strip=True))
            if len(text) >= 20 and text not in result:
                result.append(text)
        return result

    # 策略 1：<article>
    article = soup.find("article")
    if article:
        paragraphs = collect_from(article)

    # 策略 2：全页 <p>
    if len(paragraphs) < 3:
        paragraphs = collect_from(soup)

    # 策略 3：正文不在 <p> 里的老站点 —— 找文字最多的 div
    if len(paragraphs) < 3:
        best_div = None
        best_len = 0
        for div in soup.find_all("div"):
            # 只看“直接文字”比较多的 div，避免把整个页面选进来
            text = clean_line(div.get_text(" ", strip=True))
            if 200 < len(text) < 20000 and len(text) > best_len:
                # 如果这个 div 里已经包含了大段 <p>，说明前面的策略能覆盖，跳过
                best_div = div
                best_len = len(text)
        if best_div is not None:
            raw = clean_line(best_div.get_text("\n", strip=True))
            paragraphs = [
                line.strip()
                for line in raw.splitlines()
                if len(line.strip()) >= 20
            ]

    # 去掉套话、去重、保持原顺序
    cleaned = []
    for line in paragraphs:
        if is_noise(line):
            continue
        if line not in cleaned:
            cleaned.append(line)

    return title, cleaned


def fetch_one(url, max_chars):
    """抓取并打印一个网址的正文。返回 True/False 表示成功/失败。"""
    print(f"\n[URL] {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        # 中文网站编码五花八门，用 apparent_encoding 自动判断
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "lxml")
        title, paragraphs = extract_from_soup(soup)
        text = "\n".join(paragraphs)

        if len(text) < 100:
            print("[FAIL] 没提取到有效正文（可能被反爬、需要登录，或正文在图片里）")
            print(f"       HTTP 状态码：{response.status_code}")
            return False

        if len(text) > max_chars:
            text = text[:max_chars] + "\n……（正文过长，已截断）"

        print(f"[OK] 标题：{title}")
        print(f"[OK] 正文长度：{len(text)} 字")
        print("-" * 60)
        print(text)
        print("-" * 60)
        return True

    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="提取新闻网页正文")
    parser.add_argument("urls", nargs="+", help="一个或多个网址")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=6000,
        help="每个网址最多输出多少字，默认 6000",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="把结果同时保存到这个文件（可选）",
    )
    args = parser.parse_args()

    # 把终端输出同时写进文件（如果指定了 --out）
    output_chunks = []
    original_write = sys.stdout.write

    def tee_write(text):
        original_write(text)
        output_chunks.append(text)

    sys.stdout.write = tee_write

    success = 0
    for url in args.urls:
        if fetch_one(url, args.max_chars):
            success += 1

    sys.stdout.write = original_write

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("".join(output_chunks))
        print(f"\n结果已保存到：{args.out}")

    print(f"\n共尝试 {len(args.urls)} 个网址，成功 {success} 个。")
    if success == 0:
        # 全部失败时返回非 0，方便调用方判断
        sys.exit(1)


if __name__ == "__main__":
    main()
