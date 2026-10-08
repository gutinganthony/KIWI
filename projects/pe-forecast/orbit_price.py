#!/usr/bin/env python3
"""本益比軌道模型：給 EPS（你的看法，可加市場共識），算 h 個月後的本益比與股價區間（README §16）。

    python3 orbit_price.py MU --eps 70 --eps2 85                       # 12 個月後；EPS＝那時已公布的最近四季（GAAP 稀釋）
    python3 orbit_price.py MU --eps 70 --eps2 85 --cons 65 --cons2 78  # 加上市場共識（同口徑）：模型分開算「市場預期」與「你的看法」
    python3 orbit_price.py MU --fy "2027-08:72,2028-08:90" --fy-cons "2027-08:65,2028-08:80"
                                                                       # 用會計年度 EPS（年度結束月:EPS），自動換算成目標日的最近四季
    python3 orbit_price.py MU --eps 55,70,85 --eps2 70,85,100          # 悲觀／基準／樂觀（逗號分隔，一一對應）
    python3 orbit_price.py NVDA --eps 9 --h 24                         # 6、12、24 個月
    python3 orbit_price.py MU --eps 70 --eps2 90 --cons auto           # 自動抓 Yahoo 共識（本財年、下一財年；pef/consensus.py）
共識 EPS 也可以放在 data/consensus.csv（欄位：ticker, fy_end, eps, source, asof；同一年度取 asof 最新的一筆），
沒給 --cons／--fy-cons 時自動讀；你在命令列給的永遠優先。--cons auto：先用 7 天內的快照（data/consensus_snapshots/），
沒有就即時抓並存成今天的快照；再抓 quoteSummary（分析師人數、90 天修正、精確的會計年度、調整後實際 EPS），
並用「GAAP ÷ 調整後」的最近四季把共識自動換成 GAAP 口徑（--cons-scale 可以自己指定，1＝不換）。
今天的股價：先試 Yahoo（今天收盤），失敗就用 results/now_all.csv。
不是投資建議。
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus, orbit, yahoo                 # noqa: E402

RES = os.path.join(HERE, "results")


def parse_list(s):
    return [float(v) for v in s.split(",")] if s else []


def parse_fy(s):
    """"2027-08:72,2028-08:90" → {年度結束日（月底）: EPS}"""
    out = {}
    for part in (s or "").split(","):
        if part.strip():
            k, v = part.split(":")
            out[pd.Timestamp(k.strip() + ("-01" if len(k.strip()) == 7 else "")) + pd.offsets.MonthEnd(0)] = float(v)
    return out


def consensus_from_file(ticker):
    path = os.path.join(HERE, "data", "consensus.csv")
    if not os.path.exists(path):
        return {}, None
    c = pd.read_csv(path, parse_dates=["fy_end", "asof"], comment="#", dtype={"ticker": str})
    c = c[c["ticker"].fillna("").str.upper().str.replace(".", "-", regex=False) == ticker]
    if c.empty:
        return {}, None
    c = c.sort_values("asof").groupby("fy_end").tail(1)
    fy = {pd.Timestamp(r.fy_end) + pd.offsets.MonthEnd(0): float(r.eps) for r in c.itertuples()}
    return fy, f"{c['source'].iloc[-1]}，{c['asof'].max().date()}"


def today_row(t):
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end", "price_date"])
    hit = d[(d["ticker"] == t) | d["aliases"].fillna("").str.split().apply(lambda s: t in s)]
    if hit.empty:
        sys.exit(f"找不到 {t}（results/now_all.csv 只有有季報的美股）")
    row = hit.iloc[0].to_dict()
    y = yahoo.chart(t, "5d", "1d")
    if y is not None and len(y["close"]):
        new_px = float(y["close"].iloc[-1])
        if row["px"] > 0 and abs(np.log(new_px / row["px"])) < 1.0:          # 防止分割造成的口徑跳動
            row["eps0"] = row["eps0"]                                          # EPS 口徑不變（股數同為分割調整後）
            row["px"], row["price_date"] = new_px, y["close"].index[-1]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--h", type=int, default=12, choices=[6, 12, 24])
    ap.add_argument("--eps", help="你的 h 個月後 EPS（那時已公布的最近四季；逗號＝多個情境）")
    ap.add_argument("--eps2", help="你的 h＋12 個月後 EPS（同上；和 --eps 一一對應）")
    ap.add_argument("--cons", help="市場共識：h 個月後的最近四季 EPS；或 auto＝自動抓 Yahoo 共識")
    ap.add_argument("--cons2", type=float, help="市場共識：h＋12 個月後的最近四季 EPS")
    ap.add_argument("--fy", help="你的會計年度 EPS，例如 \"2027-08:72,2028-08:90\"")
    ap.add_argument("--fy-cons", help="市場共識的會計年度 EPS，格式同 --fy")
    ap.add_argument("--cons-scale", type=float, default=None,
                    help="共識乘上這個數（調整後口徑 → GAAP，例如 0.8）；--cons auto 時預設用 GAAP ÷ 調整後的最近四季自動換算")
    ap.add_argument("--erp", type=float, default=None, help="股權風險溢酬（預設 0.05）")
    a = ap.parse_args(sys.argv[1:])
    t = a.ticker.upper().replace(".", "-")
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    row = today_row(t)
    notes = []
    use_auto = str(a.cons or "").lower() == "auto"
    snap, snap_src = consensus.get_row(t, os.path.join(HERE, "data", "consensus_snapshots"), live=use_auto)
    cache = os.path.join(HERE, ".cache", "yahoo")
    qs = consensus.quote_summary(t, cache) if use_auto else None   # 完整分析師資料（要 fc.yahoo.com、query2 網域）
    rf = consensus.refresh_eps(row, snap, mrq=(qs or {}).get("mrq"))   # 快照比 now_all.csv 新、又公布了新的季 → 改用 Yahoo 的 GAAP 最近四季
    if rf["n_new"]:
        row["eps0"], row["period_end"] = rf["eps0"], rf["period_end"]
        notes.append(rf["note"])
    asof = pd.Timestamp(row["price_date"])
    ta, tb = asof + pd.DateOffset(months=a.h), asof + pd.DateOffset(months=a.h + 12)
    eps0 = float(row["eps0"])

    # 你的 EPS
    if a.fy:
        fy = parse_fy(a.fy)
        ea, how_a = orbit.calendarize(fy, ta, row["period_end"], eps0)
        eb, how_b = orbit.calendarize(fy, tb, row["period_end"], eps0)
        if ea is None:
            sys.exit(f"--fy 換算不出 {a.h} 個月後的最近四季 EPS：請多給一個會計年度，或直接用 --eps")
        mine = [(ea, eb)]
        notes.append(f"你的 EPS 由會計年度換算：a＝{how_a}；b＝{how_b or '換算不出（請多給一年或用 --eps2）'}")
    else:
        la, lb = parse_list(a.eps), parse_list(a.eps2)
        if not la:
            la = []
        if lb and len(lb) != len(la):
            sys.exit("--eps2 的個數要和 --eps 一樣")
        mine = [(v, lb[i] if lb else None) for i, v in enumerate(la)]

    # 市場共識：命令列數字（--cons／--cons2）> --fy-cons > data/consensus.csv > --cons auto（Yahoo）
    ca = None
    if a.cons is not None and not use_auto:
        try:
            ca = float(a.cons)
        except ValueError:
            sys.exit(f"--cons 要給數字或 auto（收到 {a.cons!r}）")
    cb, csrc = a.cons2, "命令列"
    fyc = parse_fy(a.fy_cons) if a.fy_cons else {}
    if fyc and ca is not None:
        notes.append("同時給了 --cons 和 --fy-cons：EPS_a 用 --cons，--fy-cons 只用在沒給 --cons2 時的 EPS_b")
    if not fyc and ca is None:
        fyc, src = consensus_from_file(t)
        if fyc:
            csrc = f"data/consensus.csv（{src}）"
            if use_auto:
                notes.append("data/consensus.csv 有這一檔 → 用檔案裡的共識，--cons auto 略過（要用 Yahoo 就先刪掉檔案裡那幾列）")
    if not fyc and ca is None and use_auto:
        au = consensus.auto(t, snap, snap_src, cache, qs=qs)
        if au is None:
            notes.append("--cons auto：Yahoo 沒有這一檔的共識（或抓不到會計年度），改用沒有共識的寫法")
        else:
            fyc, csrc = au["fy"], au["source"]
            k = [f"{e.date()} {v:,.2f}" for e, v in sorted(au["fy"].items())]
            notes.append(f"Yahoo 共識：本財年／下一財年 {'、'.join(k)}（本財年＝還沒公布的最早那一年）")
            v0 = sorted(au["fy"].items())[0][1]
            k_ok = au["basis_k"] is not None and 0.4 <= au["basis_k"] <= 1.15
            if eps0 > 0:
                notes.append(f"口徑對照：本財年共識 ÷ 目前 GAAP 最近四季 ＝ {v0 / eps0:.2f}"
                             + ("（> 1.5：可能是高成長，也可能是共識用調整後口徑——軟體、股票報酬費用高的公司通常是後者，"
                                "那就用 --cons-scale 換算）" if v0 / eps0 > 1.5 and not k_ok else ""))
            elif v0 > 0:
                notes.append("⚠ 今天 GAAP 虧損、共識卻是正的：共識幾乎一定是調整後口徑。你的 EPS 若是 GAAP，"
                             "「你和共識的差距」會被系統性低估 → 用 --cons-scale、或手動給 GAAP 口徑的共識")
            notes += ["  " + i for i in au["info"]]
            notes += ["⚠ " + w for w in au["warn"]]
            k = au["basis_k"]
            if a.cons_scale is None and k is not None:
                if 0.4 <= k <= 1.15:
                    if abs(k - 1) > 0.03:
                        a.cons_scale = k
                        notes.append(f"口徑：GAAP 最近四季 ÷ 調整後最近四季 ＝ {k:.2f} → 共識自動 × {k:.2f} 換成 GAAP"
                                     "（不要換算就加 --cons-scale 1）")
                else:
                    notes.append(f"⚠ 口徑係數 {k:.2f} 不合理（GAAP 虧損或一次性損益）→ 不自動換算；你的 EPS 若是 GAAP，請用 --cons-scale 自己換")
    if fyc:
        if ca is None:
            ca, how_ca = orbit.calendarize(fyc, ta, row["period_end"], eps0, extrapolate=True)
        else:
            how_ca = "命令列"
        if cb is None:
            cb, how_cb = orbit.calendarize(fyc, tb, row["period_end"], eps0, extrapolate=True)
        else:
            how_cb = "命令列"
        notes.append(f"共識由會計年度換算：a＝{how_ca}；b＝{how_cb}")
    if a.cons_scale is not None and a.cons_scale != 1.0:
        ca = ca * a.cons_scale if ca is not None else None
        cb = cb * a.cons_scale if cb is not None else None
        notes.append(f"共識已乘上 {a.cons_scale:.2f}（--cons-scale）")
    if not mine:
        if ca is None:
            sys.exit("請給你的 EPS（--eps／--fy），或提供市場共識（--cons 數字或 auto／--fy-cons／data/consensus.csv）")
        mine = [(ca, cb)]
        notes.append("沒有給你自己的 EPS：用市場共識當你的看法（模型只算「市場預期」那一項）")

    qa = orbit.reported_quarter(row["period_end"], ta)
    print(f"{row['ticker']}　{row['name']}")
    pe0 = f"{row['px'] / eps0:,.1f}" if eps0 > 0 else "無定義（虧損）"
    print(f"  今天（{asof.date()}）：股價 {row['px']:,.2f}、最近四季 EPS {eps0:,.2f}、本益比 {pe0}；"
          f"類型：{orbit.GNAME[orbit.group_of(row.get('sector'))]}")
    print(f"  {a.h} 個月後（{ta.date()}）：那時大概已公布到 {qa.date()} 那一季 → EPS_a＝季末 "
          f"{(qa - pd.DateOffset(months=9)).strftime('%Y-%m')}～{qa.strftime('%Y-%m')} 的四季合計；EPS_b＝再往後 12 個月（若公司實際公布得比 45 天快，可能多含一季）")
    if ca is not None:
        print(f"  市場共識（{csrc}）：EPS_a {ca:,.2f}" + (f"、EPS_b {cb:,.2f}" if cb is not None else ""))
    for n_ in notes:
        print("  " + n_)
    res = []
    for ea, eb in mine:
        o = orbit.predict(row, a.h, model, ea, eb, ca, cb, erp=a.erp)
        o["eps_a"], o["eps_b"] = ea, eb if (eb is not None and np.isfinite(eb)) else None
        res.append(o)
    o0 = res[0]
    print(f"\n  寫法：{o0['spec']}｜軌道（資金成本 − 股利，{a.h} 個月）{np.exp(o0['mk']) - 1:+.1%}｜區間寬度：波動 {o0['vol']:.0%}"
          f"{'' if o0['vol_known'] else '（沒有資料，用中位數）'}，是中位波動股票的 {o0['width']:.2f} 倍")
    print("  EPS_a     EPS_b    本益比（中位）  本益比 80% 區間     股價（中位）  股價 50% 區間        股價 80% 區間       h 個月後 forward 本益比")
    for o in res:
        pe = f"{o['pe']:10.1f}     {o['pe_lo80']:6.1f}–{o['pe_hi80']:<7.1f}" if o["pe"] else "    無定義（EPS_a ≤ 0）     "
        fwd = f"{o['fwd_pe']:.1f}" if o["fwd_pe"] else "—"
        eb_s = f"{o['eps_b']:,.2f}" if o["eps_b"] is not None else "—"
        print(f"  {o['eps_a']:>7,.2f}  {eb_s:>7}  {pe}  {o['px']:>10,.0f}   "
              f"{o['px_lo50']:>8,.0f}–{o['px_hi50']:<8,.0f}  {o['px_lo80']:>8,.0f}–{o['px_hi80']:<8,.0f}   {fwd}")
    print("\n  拆解（第一個情境）：")
    print(f"    軌道：股價 × exp({o0['mk']:+.3f})  ← 市場看法不變時的預期")
    for p in o0["parts"]:
        print(f"    {p['項目']}：{p['數值']:+.3f} × β {p['β']:+.3f} ＝ {p['影響']:+.3f}")
    if o0["widen"] > 1:
        print(f"  ⚠ EPS_a ≤ 0：本益比沒有定義（方案 A：只看股價），區間依回測放寬 ×{o0['widen']:.2f}；"
              "有給 EPS_b 時看最右欄的 forward 本益比（方案 B）")
    if o0["spec"] == "軌道" and eps0 <= 0 and o0["pe"] is not None:
        print("  注意：今天虧損、又沒有共識 → 算不了 EPS 成長率，股價只用軌道（你的 EPS 只用在本益比的分母）；"
              "給共識（--cons）時可以用「你和共識的差距」")
    if ca is None and not use_auto:
        print("  提示：加 --cons auto 可以自動抓 Yahoo 共識，模型會分開算「市場已預期的成長」和「你和市場的差距」")
    if o0["group_key"] == "cyclical" and o0["eps_b"] is None and o0["spec"] != "軌道":
        print("  提示：半導體／設備／記憶體的股價主要看「再下一年」的 EPS（回測 β_b ≈ 0.17、β_a ≈ 0）→ 建議加 --eps2")
    bt = model["backtest"].get(str(a.h), {})
    if bt:
        print(f"\n  回測（S&P 500，預測起點 2022 以後，EPS 完全正確時，中位 |ln 股價誤差|）：\n    "
              + "；".join(f"{k} {v:.3f}" for k, v in bt.items()))
    rc = (model.get("recent") or {}).get(str(a.h), {})
    if rc:
        print(f"  最近（起點 2024-10～2025-09，目標日到 2026-09）：" + "；".join(
            f"{g} 軌道 {v['軌道']:.3f}（市場偏離軌道 {v['市場偏離軌道中位']:+.2f}）" for g, v in rc.items()
            if g in ("全部", "科技", o0["group"])))
    print("  讀法：股價主要跟著軌道走；EPS 多 10% 通常只讓股價多 0.5–2%（半導體類較大、再下一年的 EPS 較重要），"
          "\n        所以本益比 ≈ 股價 ÷ 你的 EPS，主要由你的 EPS 決定。誤差最大的來源是整個產業被重新定價"
          "\n        （2025–26 年的 AI 記憶體行情、軟體股修正），模型預測不了，區間已含這部分。不是投資建議。")


if __name__ == "__main__":
    main()
