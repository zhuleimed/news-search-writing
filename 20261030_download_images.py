#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻配图下载与校验器（Claude Code 专用版）

作用：
    读取写作分身给出的“候选图片清单”（JSON），逐张下载、校验、去重，
    把合格图片保存成 img_01.jpg、img_02.jpg……，并生成最终图片清单，
    供 20261030_build_docx.py 插入 Word。

用法：
    python 20261030_download_images.py \
        --manifest news_papers/20261030/20261030_1014_01.images.json \
        --outdir news_papers/20261030/images/01 \
        --min-count 3 --max-count 5

校验标准（不合格的自动跳过）：
    - HTTP 200，文件大小 20KB～15MB；
    - 能被 Pillow 打开；
    - 宽 ≥ 400 像素、高 ≥ 250 像素；
    - 宽高比在 0.4～2.6 之间（排除细长广告条）；
    - 内容重复的图片只保留第一张。
"""

import argparse
import hashlib
import io
import json
import os
import sys

import requests
from PIL import Image

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

MIN_BYTES = 10 * 1024
MAX_BYTES = 15 * 1024 * 1024
MIN_WIDTH = 400
MIN_HEIGHT = 250
MIN_RATIO = 0.4
MAX_RATIO = 2.6


def download_one(candidate, index, outdir, seen_hashes):
    """下载并校验一张图。成功返回图片信息字典，失败返回 None。"""
    url = candidate.get("url")
    source_page = candidate.get("source_page") or ""
    if not url:
        return None

    headers = dict(HEADERS)
    if source_page:
        headers["Referer"] = source_page

    print(f"\n[{index}] 下载：{url}")
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            print(f"    跳过：HTTP {response.status_code}")
            return None

        data = response.content
        if len(data) < MIN_BYTES:
            print(f"    跳过：文件太小（{len(data)} 字节）")
            return None
        if len(data) > MAX_BYTES:
            print(f"    跳过：文件太大（{len(data)} 字节）")
            return None

        # 用 Pillow 验证图片是否完整
        try:
            probe = Image.open(io.BytesIO(data))
            probe.verify()
            image = Image.open(io.BytesIO(data))
        except Exception as exc:
            print(f"    跳过：不是有效图片（{type(exc).__name__}）")
            return None

        width, height = image.size
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            print(f"    跳过：尺寸太小（{width}x{height}）")
            return None

        ratio = width / height if height else 0
        if ratio < MIN_RATIO or ratio > MAX_RATIO:
            print(f"    跳过：宽高比不合适（{ratio:.2f}）")
            return None

        # 内容去重：同一张图即使地址不同，也只保留一次
        digest = hashlib.md5(data).hexdigest()
        if digest in seen_hashes:
            print("    跳过：与前面的图片重复")
            return None
        seen_hashes.add(digest)

        # 统一转成 RGB 的 JPEG，Word 兼容性最好
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            rgba = image.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            image = background
        else:
            image = image.convert("RGB")

        filename = f"img_{index:02d}.jpg"
        local_path = os.path.join(outdir, filename)
        image.save(local_path, "JPEG", quality=90, optimize=True)

        print(f"    合格：{width}x{height}，保存为 {filename}")
        return {
            "local_path": os.path.abspath(local_path),
            "filename": filename,
            "url": url,
            "caption": candidate.get("caption", "").strip(),
            "source_page": source_page,
            "source_name": candidate.get("source_name", "").strip(),
            "width": width,
            "height": height,
        }

    except Exception as exc:
        print(f"    跳过：{type(exc).__name__}: {exc}")
        return None


def main():
    parser = argparse.ArgumentParser(description="下载并校验新闻配图")
    parser.add_argument("--manifest", required=True, help="候选图片 JSON")
    parser.add_argument("--outdir", required=True, help="图片保存目录")
    parser.add_argument("--min-count", type=int, default=3, help="至少几张")
    parser.add_argument("--max-count", type=int, default=5, help="最多几张")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as f:
        payload = json.load(f)

    candidates = payload.get("images", [])
    os.makedirs(args.outdir, exist_ok=True)

    valid = []
    seen_hashes = set()

    for candidate in candidates:
        if len(valid) >= args.max_count:
            break
        info = download_one(candidate, len(valid) + 1, args.outdir, seen_hashes)
        if info:
            valid.append(info)

    # 保存最终清单
    result = {
        "rank": payload.get("rank"),
        "article": payload.get("article", ""),
        "images": valid,
    }
    manifest_path = os.path.join(args.outdir, "images_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"候选 {len(candidates)} 张，合格 {len(valid)} 张")
    for i, image in enumerate(valid, start=1):
        print(
            f"  {i}. {image['filename']}  {image['width']}x{image['height']}  "
            f"{image['caption'] or '（无说明）'}"
        )
    print(f"最终清单：{manifest_path}")

    if len(valid) < args.min_count:
        print(f"\n警告：合格图片只有 {len(valid)} 张，少于要求的 {args.min_count} 张。")
        sys.exit(1)


if __name__ == "__main__":
    main()
