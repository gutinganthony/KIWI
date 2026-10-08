#!/usr/bin/env python3
"""存一份市場共識 EPS 快照（Yahoo 預設產業選股器，全部類股約 3,600 檔）→ data/consensus_snapshots/yahoo_YYYY-MM-DD.csv.gz

    python3 consensus_snapshot.py              # 全部類股的本財年／下一財年共識（約 30 秒）
    python3 consensus_snapshot.py --detail     # 另存 S&P 500＋科技＋Nasdaq-100（約 460 檔）的完整分析師資料（約 10 分鐘）
                                               # → data/consensus_snapshots/yahoo_detail_YYYY-MM-DD.csv.gz

每週跑一次，累積下來就是我們自己的「歷史時點」共識（research/06 §4.2）：以後可以用真正的共識重估
orbit 模型的 β_e、β_s（現在是用代理預期估的，README §16.5）。同一天重跑會覆蓋當天的檔。
欄位：asof_utc、screener、symbol、epsCurrentYear（本財年 0y）、epsForward（下一財年 +1y）、epsTrailingTwelveMonths（GAAP）…
--detail（quoteSummary，要 fc.yahoo.com、query2.finance.yahoo.com）：last_fy（最近已公布年度）、mrq（最近一季）、street_ttm（調整後最近四季）、
  0q／+1q／0y／+1y 各自的 avg、low、high、n（分析師人數）、d7／d30／d60／d90（幾天前的共識）、up30／down30（30 天上修／下修人數）。
  有 d7–d90，第一份快照就自帶 90 天的修正歷史。
"""
import argparse
import os
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus                                # noqa: E402

SNAP = os.path.join(HERE, "data", "consensus_snapshots")


def detail(pause=1.0):
    u = pd.read_csv(os.path.join(HERE, "results", "now_all.csv"))
    u = u[(u["in_sp500"] == True) | (u["in_tech"] == True) | (u["in_ndx"] == True)]  # noqa: E712
    rows, fail, asof = [], [], pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%MZ")
    for i, t in enumerate(sorted(u["ticker"].unique())):
        q = consensus.quote_summary(t, os.path.join(HERE, ".cache", "yahoo"), max_age_h=12)
        if q is None:
            fail.append(t)
            if len(fail) >= 20 and len(fail) > 0.5 * (i + 1):
                sys.exit(f"失敗太多（{len(fail)}／{i + 1}），可能被限流或 cookie 失效；已停止")
        else:
            r = dict(asof_utc=asof, symbol=consensus.yahoo_symbol(t), last_fy=q["last_fy"], mrq=q["mrq"], street_ttm=q["street_ttm"])
            for p in ("0q", "+1q", "0y", "+1y"):
                for k, v in (q["trend"].get(p) or {}).items():
                    r[f"{p}_{k}"] = v
            rows.append(r)
        time.sleep(pause)
    d = pd.DataFrame(rows)
    path = os.path.join(SNAP, f"yahoo_detail_{asof[:10]}.csv.gz")
    os.makedirs(SNAP, exist_ok=True)
    d.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    print(f"{len(d):,} 檔（失敗 {len(fail)}：{' '.join(fail[:15])}{' …' if len(fail) > 15 else ''}）→ {os.path.relpath(path, HERE)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", action="store_true", help="另存 quoteSummary 的完整分析師資料（S&P 500＋科技＋Nasdaq-100）")
    a = ap.parse_args()
    if a.detail:
        return detail()
    d = consensus.snapshot()
    if not len(d):
        sys.exit("沒有抓到任何資料（Yahoo 可能改版或限流）")
    path = consensus.save_snapshot(d, SNAP)
    ok = d["epsForward"].notna().sum()
    print(f"{len(d):,} 檔（其中 {ok:,} 檔有下一財年共識）→ {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()
