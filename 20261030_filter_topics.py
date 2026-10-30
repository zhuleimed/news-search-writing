#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度热榜选题过滤器（Claude Code 专用版）

作用：
    从采集脚本生成的 50 条工作清单里，按用户规则筛掉不适合写的条目：
        1. 涉政类：党的会议、公报、领导人、从严治党、党史、外交/国防等；
        2. 股市实时行情类：开盘/收盘/涨跌/涨停/跌停/指数点位等；
    保留财政、金融、公司财报、消费金融等“财经类”新闻。

用法：
    python 20261030_filter_topics.py \
        --worklist news_title/baidu_20261030_10-14_50.json \
        --out news_title/baidu_20261030_10-14_50_filtered.json

输出：
    - 终端打印一张分类表；
    - 一个 JSON：包含 kept（保留，带 batch_index）和 excluded（剔除，带原因）。
"""

import argparse
import json
import os
import re

# ====================== 规则 ======================
# 涉政关键词：标题或摘要命中任意一个，就剔除。
# 注意：这里宁可多剔，不可漏剔；用户明确要求“涉政类直接取消”。
POLITICAL_PATTERNS = [
    "全会", "公报", "中共中央", "党中央", "从严治党", "党建",
    "习近平", "总书记", "政治局", "纪委", "监委", "党史",
    "红军", "长征", "国民党", "第一书记", "外交部", "国防部",
    "台海", "涉台", "涉港", "涉疆", "涉藏", "安倍", "首相",
    "总统", "大选", "议会", "政府工作报告",
]

# 股市实时行情关键词：标题命中任意一个，就剔除。
# 注意：公司财报、养老金、消费金融等“财经新闻”不在剔除范围。
MARKET_PATTERNS = [
    "开盘", "收盘", "低开", "高开", "涨超", "跌超", "涨停", "跌停",
    "沪指", "深证成指", "创业板指", "科创50", "KOSPI", "韩股",
    "恒生指数", "纳斯达克指数", "道琼斯", "标普500",
]

# 财经类关键词：命中则标记为 finance（保留，便于索引里分类）。
FINANCE_PATTERNS = [
    "养老金", "财报", "净利", "营收", "银行", "保险", "基金",
    "债券", "利率", "汇率", "货币政策", "财政", "税", "贷款",
    "存款", "支付", "消费金融", "融资", "市值", "股价", "投资",
    "理财", "钱包",
]

# 个别“关键词规则抓不住”的条目，用标题片段手动剔除。
# 每条写清楚原因，方便以后复核。
MANUAL_EXCLUDE = {
    "皇马因中国赞助": "涉外敏感：涉及中国赞助商与球员事件的表态",
}


def match_any(text, patterns):
    """返回命中的第一个关键词；没命中返回 None。"""
    for pattern in patterns:
        if pattern in text:
            return pattern
    return None


def classify(item):
    """
    给一条热点分类。

    返回 (category, reason, keep)：
        category: political / market_realtime / finance / other
        reason:   剔除原因（保留时为空）
        keep:     True 表示保留
    """
    text = f"{item.get('title', '')} {item.get('summary', '')}"

    # 1) 涉政优先剔除
    hit = match_any(text, POLITICAL_PATTERNS)
    if hit:
        return "political", f"涉政关键词：{hit}", False

    # 2) 股市实时行情剔除
    hit = match_any(text, MARKET_PATTERNS)
    if hit:
        return "market_realtime", f"股市实时行情关键词：{hit}", False

    # 3) 手动剔除
    for fragment, reason in MANUAL_EXCLUDE.items():
        if fragment and fragment in text:
            return "political", f"手动剔除：{reason}", False

    # 4) 财经类保留
    hit = match_any(text, FINANCE_PATTERNS)
    if hit:
        return "finance", "", True

    # 5) 其他保留
    return "other", "", True


def main():
    parser = argparse.ArgumentParser(description="按规则过滤百度热榜选题")
    parser.add_argument("--worklist", required=True, help="采集脚本生成的 JSON")
    parser.add_argument("--out", required=True, help="输出过滤后的 JSON")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="只保留前 N 条（不填则保留全部）",
    )
    args = parser.parse_args()

    with open(args.worklist, "r", encoding="utf-8") as f:
        payload = json.load(f)

    items = payload.get("items", [])
    kept = []
    excluded = []

    for item in items:
        category, reason, keep = classify(item)
        if keep:
            kept.append({
                **item,
                "category": category,
                "batch_index": len(kept) + 1,
            })
        else:
            excluded.append({
                "rank": item.get("rank"),
                "title": item.get("title"),
                "category": category,
                "reason": reason,
            })

    if args.limit is not None:
        kept = kept[: args.limit]
        for i, item in enumerate(kept, start=1):
            item["batch_index"] = i

    # 终端分类表
    print(f"原始条数：{len(items)}")
    print(f"保留：{len(kept)} 条；剔除：{len(excluded)} 条")
    print("=" * 100)
    print(f"{'榜单排名':<8}{'本次序号':<8}{'分类':<16}{'标题'}")
    print("-" * 100)
    for item in kept:
        print(
            f"{item['rank']:<8}{item['batch_index']:<8}"
            f"{item['category']:<16}{item['title']}"
        )

    if excluded:
        print("\n剔除明细：")
        for item in excluded:
            print(f"  - 第 {item['rank']} 名《{item['title']}》：{item['reason']}")

    # 保存 JSON
    out_payload = {
        "meta": {
            **payload.get("meta", {}),
            "filtered_at": payload.get("meta", {}).get("collected_at", ""),
            "kept_count": len(kept),
            "excluded_count": len(excluded),
        },
        "kept": kept,
        "excluded": excluded,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)

    print(f"\n过滤结果已保存：{args.out}")


if __name__ == "__main__":
    main()
