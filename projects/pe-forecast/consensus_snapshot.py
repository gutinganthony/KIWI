#!/usr/bin/env python3
"""存一份市場共識 EPS 快照（Yahoo 預設產業選股器，全部類股約 3,600 檔）→ data/consensus_snapshots/yahoo_YYYY-MM-DD.csv.gz

    python3 consensus_snapshot.py

每週跑一次，累積下來就是我們自己的「歷史時點」共識（research/06 §4.2）：以後可以用真正的共識重估
orbit 模型的 β_e、β_s（現在是用代理預期估的，README §16.5）。同一天重跑會覆蓋當天的檔。
欄位：asof_utc、screener、symbol、epsCurrentYear（本財年 0y）、epsForward（下一財年 +1y）、epsTrailingTwelveMonths（GAAP）…
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus                                # noqa: E402

SNAP = os.path.join(HERE, "data", "consensus_snapshots")


def main():
    d = consensus.snapshot()
    if not len(d):
        sys.exit("沒有抓到任何資料（Yahoo 可能改版或限流）")
    path = consensus.save_snapshot(d, SNAP)
    ok = d["epsForward"].notna().sum()
    print(f"{len(d):,} 檔（其中 {ok:,} 檔有下一財年共識）→ {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()
