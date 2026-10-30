#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度热榜采集器（Claude Code 专用版）

作用：
    1. 抓取百度热榜（https://top.baidu.com/board?tab=realtime）的前 N 条；
    2. 保存一份“人看的”TXT（标题 + 摘要），格式和旧代码一致；
    3. 保存一份“程序用的”JSON（排名、标题、摘要、百度搜索链接），
       供后续 Claude Code 逐条检索、写作使用。

特点：
    - 只做抓取，不调用任何 AI API，不需要任何 API Key；
    - 默认取前 50 条；本次可以用 --limit 10 只取前 10 条；
    - 类名用“包含匹配”（category-wrap / content_ / title_ / hot-desc），
      百度前端改哈希后缀时不容易失效。

用法示例：
    python 20261030_collect_hot50.py --limit 50
    python 20261030_collect_hot50.py --limit 10
"""

import argparse
import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ====================== 路径与常量 ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_TITLE_DIR = os.path.join(BASE_DIR, "news_title")
DEFAULT_URL = "https://top.baidu.com/board?tab=realtime"

# 模拟浏览器访问，避免被百度当成爬虫拦截
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.baidu.com/",
    "Connection": "keep-alive",
}


def clean_text(text):
    """把多余的空格、换行压成一个空格，去掉首尾空白。"""
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_html(url):
    """下载网页 HTML；失败时直接抛异常，让调用方知道抓取失败。"""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"  # 百度热榜页面是 UTF-8
    return response.text


def parse_items(html):
    """
    从百度热榜 HTML 中解析出每一条新闻。

    返回列表，每一项是一个字典：
        {"title": 标题, "summary": 摘要, "baidu_url": 百度搜索链接}
    """
    soup = BeautifulSoup(html, "lxml")
    items = []

    # 每条新闻都包在 class 含 "category-wrap" 的 div 里
    wraps = soup.find_all("div", class_=lambda c: c and "category-wrap" in c)

    for wrap in wraps:
        # ---------- 1. 定位内容区 ----------
        content = wrap.find("div", class_=lambda c: c and "content_" in c)
        if not content:
            continue

        # ---------- 2. 定位标题链接 ----------
        link = content.find("a", class_=lambda c: c and "title_" in c)
        if not link:
            continue

        title_div = link.find(
            "div", class_=lambda c: c and "c-single-text-ellipsis" in c
        )
        if not title_div:
            continue

        # 百度有时会在标题后面加“新 / 热 / 爆 / 沸”角标（span）。
        # 先把这类角标删掉，避免标题末尾多出一个字。
        for span in title_div.find_all("span"):
            if clean_text(span.get_text()) in {"新", "热", "爆", "沸", "荐"}:
                span.decompose()

        title = clean_text(title_div.get_text(" ", strip=True))

        # ---------- 3. 定位摘要 ----------
        desc_div = content.find("div", class_=lambda c: c and "hot-desc" in c)
        if desc_div:
            summary = clean_text(desc_div.get_text(" ", strip=True))
            # 去掉摘要末尾的“查看更多>”
            summary = re.sub(r"查看更多\s*[>＞]*$", "", summary).strip()
            summary = re.sub(r"[>＞]+$", "", summary).strip()
        else:
            summary = "无摘要"

        if not summary:
            summary = "无摘要"

        # ---------- 4. 百度搜索链接 ----------
        # 这个链接是“百度对该热点的搜索结果页”，后续写作时可以作为线索入口
        href = link.get("href") or ""

        if title:
            items.append(
                {"title": title, "summary": summary, "baidu_url": href}
            )

    return items


def save_txt(items, path):
    """保存成人看的 TXT，格式与旧代码保持一致：标题: XXX / 摘要: XXX。"""
    lines = []
    for item in items:
        lines.append(f"标题: {item['title']}")
        lines.append(f"摘要: {item['summary']}")
        lines.append("")  # 每条之间空一行
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def save_json(items, path, meta):
    """保存成程序用的 JSON 工作清单。"""
    payload = {"meta": meta, "items": items}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="抓取百度热榜前 N 条")
    parser.add_argument(
        "--limit", type=int, default=50, help="抓取条数，默认 50"
    )
    parser.add_argument(
        "--url", default=DEFAULT_URL, help="热榜地址，默认百度实时热榜"
    )
    args = parser.parse_args()

    # 固定本次运行的时间戳：
    #   file_stamp 用在文件名里（带横线，方便人看）
    #   run_stamp  用在后续成稿文件名里（不带分隔符，方便程序拼接）
    now = datetime.now()
    file_stamp = now.strftime("%Y%m%d_%H-%M")
    run_stamp = now.strftime("%Y%m%d_%H%M")

    print(f"[1/3] 正在抓取：{args.url}")
    html = fetch_html(args.url)

    print("[2/3] 正在解析标题和摘要……")
    all_items = parse_items(html)
    print(f"      页面共解析到 {len(all_items)} 条")

    items = all_items[: args.limit]
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank

    os.makedirs(NEWS_TITLE_DIR, exist_ok=True)
    txt_path = os.path.join(
        NEWS_TITLE_DIR, f"baidu_{file_stamp}_{len(items)}.txt"
    )
    json_path = os.path.join(
        NEWS_TITLE_DIR, f"baidu_{file_stamp}_{len(items)}.json"
    )

    save_txt(items, txt_path)
    meta = {
        "collected_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "run_stamp": run_stamp,
        "source_url": args.url,
        "total_on_page": len(all_items),
        "saved_count": len(items),
        "limit": args.limit,
    }
    save_json(items, json_path, meta)

    print(f"[3/3] 保存完成：")
    print(f"      标题摘要：{txt_path}")
    print(f"      工作清单：{json_path}")
    print(f"      运行时间戳（成稿文件名用）：{run_stamp}")
    print("\n前 5 条预览：")
    for item in items[:5]:
        print(f"  {item['rank']}. {item['title']}")
        print(f"     摘要：{item['summary'][:60]}")


if __name__ == "__main__":
    main()
