#!/usr/bin/env python3
"""本益比軌道模型：給 EPS（你的看法，可加市場共識），算 h 個月後的本益比與股價區間（README §16）。

    python3 orbit_price.py MU --eps 70 --eps2 85                       # 12 個月後；EPS＝那時已公布的最近四季（GAAP 稀釋）
    python3 orbit_price.py MU --eps 70 --eps2 85 --cons 65 --cons2 78  # 加上市場共識（同口徑）：模型分開算「市場預期」與「你的看法」
    python3 orbit_price.py MU --fy "2027-08:72,2028-08:90" --fy-cons "2027-08:65,2028-08:80"
                                                                       # 用會計年度 EPS（年度結束月:EPS），自動換算成目標日的最近四季
    python3 orbit_price.py MU --eps 55,70,85 --eps2 70,85,100          # 悲觀／基準／樂觀（逗號分隔，一一對應）
    python3 orbit_price.py NVDA --eps 9 --h 24                         # 6、12、24 個月
共識 EPS 也可以放在 data/consensus.csv（欄位：ticker, fy_end, eps, source, asof；同一年度取 asof 最新的一筆），
沒給 --cons／--fy-cons 時自動讀；你在命令列給的永遠優先。今天的股價：先試 Yahoo（今天收盤），失敗就用 results/now_all.csv。
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
from pef import orbit, yahoo                            # noqa: E402

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
    ap.add_argument("--cons", type=float, help="市場共識：h 個月後的最近四季 EPS")
    ap.add_argument("--cons2", type=float, help="市場共識：h＋12 個月後的最近四季 EPS")
    ap.add_argument("--fy", help="你的會計年度 EPS，例如 \"2027-08:72,2028-08:90\"")
    ap.add_argument("--fy-cons", help="市場共識的會計年度 EPS，格式同 --fy")
    ap.add_argument("--erp", type=float, default=None, help="股權風險溢酬（預設 0.05）")
    a = ap.parse_args(sys.argv[1:])
    t = a.ticker.upper().replace(".", "-")
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    row = today_row(t)
    asof = pd.Timestamp(row["price_date"])
    ta, tb = asof + pd.DateOffset(months=a.h), asof + pd.DateOffset(months=a.h + 12)
    eps0 = float(row["eps0"])
    notes = []

    # 你的 EPS
    if a.fy:
        fy = parse_fy(a.fy)
        ea, how_a = orbit.calendarize(fy, ta, row["period_end"], eps0)
        eb, how_b = orbit.calendarize(fy, tb, row["period_end"], eps0)
        mine = [(ea, eb)]
        notes.append(f"你的 EPS 由會計年度換算：a＝{how_a}；b＝{how_b}")
    else:
        la, lb = parse_list(a.eps), parse_list(a.eps2)
        if not la:
            la = []
        if lb and len(lb) != len(la):
            sys.exit("--eps2 的個數要和 --eps 一樣")
        mine = [(v, lb[i] if lb else None) for i, v in enumerate(la)]

    # 市場共識
    ca, cb, csrc = a.cons, a.cons2, "命令列"
    fyc = parse_fy(a.fy_cons) if a.fy_cons else {}
    if not fyc and ca is None:
        fyc, src = consensus_from_file(t)
        if fyc:
            csrc = f"data/consensus.csv（{src}）"
    if fyc:
        ca, how_ca = orbit.calendarize(fyc, ta, row["period_end"], eps0)
        cb, how_cb = orbit.calendarize(fyc, tb, row["period_end"], eps0)
        notes.append(f"共識由會計年度換算：a＝{how_ca}；b＝{how_cb}")
    if not mine:
        if ca is None:
            sys.exit("請給你的 EPS（--eps／--fy），或提供市場共識（--cons／--fy-cons／data/consensus.csv）")
        mine = [(ca, cb)]
        notes.append("沒有給你自己的 EPS：用市場共識當你的看法（模型只算「市場預期」那一項）")

    qa = orbit.reported_quarter(row["period_end"], ta)
    print(f"{row['ticker']}　{row['name']}")
    print(f"  今天（{asof.date()}）：股價 {row['px']:,.2f}、最近四季 EPS {eps0:,.2f}、本益比 "
          f"{row['px'] / eps0 if eps0 > 0 else float('nan'):,.1f}；類型：{orbit.GNAME[orbit.group_of(row.get('sector'))]}")
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
