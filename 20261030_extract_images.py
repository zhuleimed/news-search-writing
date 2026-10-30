#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻网页配图提取器（Claude Code 专用版）

作用：
    打开一篇新闻网页，把页面里的图片地址列出来，供写作分身挑选 3～5 张
    与文章内容相关的配图。

用法：
    python 20261030_extract_images.py "网页1" "网页2" --max 15
    python 20261030_extract_images.py "网页1" --json

输出：
    - 默认：人看的列表（编号、图片地址、alt 文字、来源页）；
    - 加 --json：输出 JSON，方便程序继续处理。

注意：
    - 这里只“列出”图片地址，不下载；下载和校验由
      20261030_download_images.py 负责；
    - 会过滤掉明显的 logo、图标、二维码、头像、广告位等；
    - 有些网站用懒加载（data-src），脚本已经兼容。
"""

import argparse
import json
import re
from urllib.parse import urljoin

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
}

# 图片地址里出现这些词，基本可以判断是网站装饰，不是新闻配图
BAD_URL_PATTERNS = [
    "logo", "icon", "avatar", "headimg", "qrcode", "qr_", "erweima",
    "share", "weixin", "weibo", "advert", "banner", "spacer", "blank",
    "pixel", "loading", "placeholder", "emoji", "sprite", "button",
    "bg_", "background", "default", "noimage", "grey.gif",
]


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def pick_src(img):
    """从 <img> 里找最可能的真实图片地址（兼容懒加载和 srcset）。"""
    # 常见的懒加载属性，优先级从高到低
    for attr in [
        "data-src", "data-original", "data-lazy-src", "data-url",
        "data-original-src", "src",
    ]:
        value = img.get(attr)
        if value and not value.startswith("data:"):
            return value

    # srcset 里通常最后一个分辨率最高
    srcset = img.get("srcset") or img.get("data-srcset")
    if srcset:
        parts = [p.strip().split(" ")[0] for p in srcset.split(",") if p.strip()]
        if parts:
            return parts[-1]

    return None


def is_bad_url(url):
    low = url.lower()
    if any(pattern in low for pattern in BAD_URL_PATTERNS):
        return True
    # svg 图标和 gif 动图一般不是新闻配图；gif 偶尔可用，这里先排除
    if low.endswith(".svg") or low.endswith(".gif"):
        return True
    return False


def extract_from_page(url, max_images):
    """抓一个页面，返回 (页面标题, 候选图片列表)。"""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "lxml")

    title = clean_text(soup.title.get_text()) if soup.title else ""

    candidates = []
    seen = set()

    # 1) og:image / twitter:image，通常是正文主图
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        if prop in {"og:image", "og:image:url", "twitter:image"}:
            src = meta.get("content")
            if src:
                src = urljoin(url, src)
                if src.startswith(("http://", "https://")) and not is_bad_url(src):
                    if src not in seen:
                        seen.add(src)
                        candidates.append({
                            "url": src,
                            "alt": "页面主图",
                            "width": None,
                            "height": None,
                            "source_page": url,
                        })

    # 2) 页面里的 <img>
    for img in soup.find_all("img"):
        src = pick_src(img)
        if not src:
            continue
        src = urljoin(url, src)
        if not src.startswith(("http://", "https://")):
            continue
        if is_bad_url(src) or src in seen:
            continue

        seen.add(src)
        candidates.append({
            "url": src,
            "alt": clean_text(img.get("alt")),
            "width": img.get("width"),
            "height": img.get("height"),
            "source_page": url,
        })

        if len(candidates) >= max_images:
            break

    return title, candidates[:max_images]


def main():
    parser = argparse.ArgumentParser(description="列出新闻网页里的图片地址")
    parser.add_argument("urls", nargs="+", help="一个或多个网页地址")
    parser.add_argument("--max", type=int, default=15, help="每个页面最多列几张")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--out", default=None, help="把 JSON 保存到文件")
    args = parser.parse_args()

    results = []
    for url in args.urls:
        try:
            title, images = extract_from_page(url, args.max)
            results.append({
                "source_page": url,
                "title": title,
                "images": images,
            })
        except Exception as exc:
            results.append({
                "source_page": url,
                "title": "",
                "images": [],
                "error": f"{type(exc).__name__}: {exc}",
            })

    if args.json:
        text = json.dumps(results, ensure_ascii=False, indent=2)
        print(text)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
        return

    # 人看的格式
    for page in results:
        print(f"\n[页面] {page['source_page']}")
        print(f"[标题] {page['title']}")
        if page.get("error"):
            print(f"[失败] {page['error']}")
            continue
        if not page["images"]:
            print("  （没有找到候选图片）")
            continue
        for i, image in enumerate(page["images"], start=1):
            alt = image["alt"] or "（无 alt）"
            print(f"  {i:2d}. {image['url']}")
            print(f"      alt：{alt}")


if __name__ == "__main__":
    main()
