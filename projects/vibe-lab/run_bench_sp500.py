#!/usr/bin/env python3
"""alpha101 × S&P 500 bench runner for vibe-trading（KIWI vibe-lab）.

為什麼需要這支 wrapper（而不是直接 `vibe-trading alpha bench`）：
雲端容器的 egress proxy 擋掉 en.wikipedia.org，vibe-trading 的
_fetch_sp500_constituents() 會靜默降級成內建 50 檔 hand-picked 清單
（輸出會標 "degraded run"，等於只 bench 50 檔大型股）。本 wrapper：

  1. 把真正的 S&P 500 成分股清單（data/constituents.csv，來源
     github.com/datasets/s-and-p-500-companies 的每日快照）餵給它；
  2. 往 panel 注入 panel["sector"]（同 CSV 的 GICS Sector，與 close 同形狀、
     整欄常值），讓 20 支 requires_sector 的行業中性化因子可以跑，
     而不是被 SkipAlpha 跳過；
  3. 其餘流程原封不動走官方 CLI handler（cmd_alpha_bench）。

用法（任何目錄皆可）：
  python3 projects/vibe-lab/run_bench_sp500.py \
      --period 2020-01-01/2026-07-10 --top 101 [--zoo alpha101] [--fresh]

已知限制（報告判讀時必記）：
  - 用「今日成分股」回測歷史 = survivorship bias，IC 系統性偏高
    （vibe-trading 官方 wiki 同樣警告；point-in-time membership 是其 planned 功能）。
  - sector 標籤用「今日 GICS sector」套整段歷史（期間內換版塊的公司會標錯）。
  - --fresh 會先清 ~/.vibe-trading/cache/ 的 sp500 panel 快取；
    改過成分清單之後第一次跑必須帶 --fresh，否則會命中舊清單的快取。
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description="alpha bench with real S&P 500 constituents")
    ap.add_argument("--constituents", default=str(HERE / "data" / "constituents.csv"))
    ap.add_argument("--zoo", default="alpha101")
    ap.add_argument("--period", default="2020-01-01/2026-07-10")
    ap.add_argument("--top", type=int, default=101)
    ap.add_argument("--fresh", action="store_true", help="purge cached sp500 panels before run")
    args = ap.parse_args()

    with open(args.constituents, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # yfinance 慣例：BRK.B → BRK-B
    codes = [r["Symbol"].strip().replace(".", "-") for r in rows if r.get("Symbol", "").strip()]
    sectors = {
        r["Symbol"].strip().replace(".", "-"): (r.get("GICS Sector") or "Unknown").strip()
        for r in rows
    }
    if len(codes) < 400:
        sys.exit(f"constituents list suspiciously short ({len(codes)}); refusing degraded run")
    print(f"[wrapper] {len(codes)} constituents ← {args.constituents}")

    import src.tools.alpha_bench_tool as abt

    if args.fresh:
        cache_dir = pathlib.Path.home() / ".vibe-trading" / "cache"
        for p in sorted(cache_dir.glob("sp500_*")):
            print(f"[wrapper] purge cache: {p.name}")
            p.unlink()

    abt._fetch_sp500_constituents = lambda: list(codes)
    abt._SP500_CONSTITUENT_SOURCE_DATE = "2026-07-12 github.com/datasets/s-and-p-500-companies"

    original_load = abt._load_sp500_panel

    def load_with_sector(start: str, end: str):
        panel = original_load(start, end)
        close = panel.get("close")
        if close is not None:
            import pandas as pd

            col_sector = {}
            for col in close.columns:
                sym = col[:-3] if col.upper().endswith(".US") else col
                col_sector[col] = sectors.get(sym, "Unknown")
            panel["sector"] = pd.DataFrame(
                {c: [col_sector[c]] * len(close.index) for c in close.columns},
                index=close.index,
            )
            n_unknown = sum(1 for v in col_sector.values() if v == "Unknown")
            print(f"[wrapper] sector tags injected: {len(close.columns)} cols, {n_unknown} unknown")
        return panel

    abt._load_sp500_panel = load_with_sector

    from backtest.loaders.registry import resolve_loader

    loader = resolve_loader("us_equity")
    print(f"[wrapper] us_equity loader → {type(loader).__module__}.{type(loader).__name__}")

    from src.factors.cli_handlers import cmd_alpha_bench

    ns = argparse.Namespace(
        zoo=args.zoo, universe="sp500", period=args.period, top=args.top, yes=True
    )
    return cmd_alpha_bench(ns)


if __name__ == "__main__":
    raise SystemExit(main())
