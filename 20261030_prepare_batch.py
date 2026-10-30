#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把“选题评审结果”和“原始榜单”合并成写作批次清单。

为什么需要这一步：
    选题主编输出的 selected.json 只有 rank/title/score/reason，
    没有摘要和百度搜索链接；写作分身还需要 summary、baidu_url，
    质检脚本也需要一个带 batch_index 的 kept 列表。
    这个脚本负责把两边合并，生成 selected10_full.json。

用法：
    python 20261030_prepare_batch.py \
        --worklist news_title/baidu_20261030_10-14_50.json \
        --selection news_title/baidu_20261030_10-14_selected10.json \
        --out news_title/baidu_20261030_10-14_selected10_full.json

输入：
    --worklist   采集脚本生成的原始 JSON（items 列表，含 rank/title/summary/baidu_url）
    --selection  选题主编生成的 JSON（selected 列表，含 batch_index/rank/score/reason）

输出：
    {
      "meta": {...},
      "kept": [
        {rank, title, summary, baidu_url, category, batch_index, score, selection_reason}
      ]
    }

注意：
    - batch_index 必须从 1 开始连续、不重复；
    - 这里只合并 selected，不合并 backups；备选仍在 selection JSON 里，
      写作时资料/配图不足再从 backups 递补。
"""

import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser(description="合并选题结果与原始榜单")
    parser.add_argument("--worklist", required=True, help="原始榜单 JSON")
    parser.add_argument("--selection", required=True, help="选题评审 JSON")
    parser.add_argument("--out", required=True, help="输出写作批次 JSON")
    args = parser.parse_args()

    with open(args.worklist, "r", encoding="utf-8") as f:
        worklist = json.load(f)
    with open(args.selection, "r", encoding="utf-8") as f:
        selection = json.load(f)

    original = {item["rank"]: item for item in worklist.get("items", [])}
    selected = selection.get("selected", [])

    if not selected:
        raise SystemExit("selection 里没有 selected，请先完成选题评审")

    kept = []
    for item in selected:
        rank = item.get("rank")
        original_item = original.get(rank)
        if not original_item:
            raise SystemExit(f"原始榜单里找不到 rank={rank} 的条目")

        kept.append({
            **original_item,
            "batch_index": item.get("batch_index"),
            "category": item.get("category", ""),
            "score": item.get("score"),
            "selection_reason": item.get("reason", ""),
        })

    # 按 batch_index 排序，并检查连续性
    kept.sort(key=lambda x: x.get("batch_index") or 0)
    indexes = [item.get("batch_index") for item in kept]
    expected = list(range(1, len(kept) + 1))
    if indexes != expected:
        raise SystemExit(
            f"batch_index 必须从 1 连续到 {len(kept)}，当前是 {indexes}"
        )

    payload = {
        "meta": {
            "worklist": os.path.basename(args.worklist),
            "selection": os.path.basename(args.selection),
            "count": len(kept),
            "backups": len(selection.get("backups", [])),
        },
        "kept": kept,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"已生成写作批次：{args.out}")
    print(f"选中 {len(kept)} 条，备选 {len(selection.get('backups', []))} 条")
    for item in kept:
        print(
            f"{item['batch_index']:2d}. 榜单{item['rank']:2d} | "
            f"{item.get('category', ''):10s} | {item['title']}"
        )


if __name__ == "__main__":
    main()
