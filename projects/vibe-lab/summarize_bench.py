#!/usr/bin/env python3
"""把 run_bench_sp500.py / vibe-trading alpha bench 的輸出整理成 Markdown 摘要。

用法：
  python3 summarize_bench.py <bench輸出檔（wrapper stdout，可含非JSON前後綴）> [--top 15]
輸出寫 stdout（Markdown 片段：設定行、Top/Bottom 表、主題統計、IC 分佈）。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys


def load_bench(path: str) -> dict:
    raw = open(path, encoding="utf-8").read()
    start = raw.index("{")
    end = raw.rindex("}") + 1
    return json.loads(raw[start:end])


def fmt_row(rank: int, r: dict) -> str:
    themes = "/".join(r.get("theme") or [])
    return (
        f"| {rank} | {r['id']} | {themes} | {r['ic_mean']:+.4f} | {r['ic_std']:.3f} "
        f"| {r['ir']:+.4f} | {r['ic_positive_ratio']:.3f} | {r['ic_count']} |"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_out")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    data = load_bench(args.bench_out)
    rows = data["top"]
    if not rows:
        print("（無結果列）")
        return 1

    ics = [r["ic_mean"] for r in rows]
    irs = [r["ir"] for r in rows]
    header = (
        "| # | Alpha | 主題 | IC mean | IC std | IR(日) | IC+比率 | N |\n"
        "|---|---|---|---|---|---|---|---|"
    )

    print(f"- zoo `{data['zoo']}` × universe `{data['universe']}` × period `{data['period']}`")
    print(f"- 測得 {data['n_alphas_tested']} 支、跳過 {data['n_skipped']} 支；wall {data['wall_seconds']:.0f}s")
    print(
        f"- IC mean 分佈：中位 {statistics.median(ics):+.4f}，"
        f"範圍 [{min(ics):+.4f}, {max(ics):+.4f}]；"
        f"日 IR 中位 {statistics.median(irs):+.4f}，|IR|>0.03 共 "
        f"{sum(1 for x in irs if abs(x) > 0.03)} 支"
    )
    cats: dict[str, int] = {}
    for r in rows:
        c = r.get("category", "?")
        cats[c] = cats.get(c, 0) + 1
    print(f"- 工具存活判定：{cats}")

    print(f"\n**Top {args.top} by 日 IR**\n\n{header}")
    for i, r in enumerate(rows[: args.top], 1):
        print(fmt_row(i, r))

    print(f"\n**Bottom 5 by 日 IR**\n\n{header}")
    n = len(rows)
    for i, r in enumerate(rows[-5:], n - 4):
        print(fmt_row(i, r))

    # 主題聚合（一支因子可屬多主題，重複計入）
    theme_ics: dict[str, list[float]] = {}
    for r in rows:
        for t in r.get("theme") or ["untagged"]:
            theme_ics.setdefault(t, []).append(r["ic_mean"])
    print("\n**主題聚合（IC mean 中位數）**\n\n| 主題 | 支數 | IC 中位 |\n|---|---|---|")
    for t, v in sorted(theme_ics.items(), key=lambda kv: -statistics.median(kv[1])):
        print(f"| {t} | {len(v)} | {statistics.median(v):+.4f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
